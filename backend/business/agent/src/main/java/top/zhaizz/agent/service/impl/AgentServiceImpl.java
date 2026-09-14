package top.zhaizz.agent.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.agent.constant.TraceConstants;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.Result;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

/**
 * HTTP Agent 服务：转发请求到 Python agent，统一归类上游错误。
 */
@Slf4j
public class AgentServiceImpl implements AgentService {

    /** 用于普通 Agent 请求的 HTTP 客户端。 */
    private final RestTemplate restTemplate;
    /** 用于序列化和反序列化 JSON。 */
    private final ObjectMapper objectMapper;
    /** Agent 服务的基础 URL。 */
    private final String baseUrl;
    /** 连接 Agent 的超时时长，单位毫秒。 */
    private final long connectTimeout;
    /** 用于 SSE 请求的 HTTP 客户端。 */
    private volatile RestTemplate streamRestTemplate;

    /**
     * 创建 Agent HTTP 代理服务。
     * @param restTemplate 普通请求客户端
     * @param objectMapper 请求响应序列化器
     * @param baseUrl Agent 服务地址
     * @param connectTimeout 连接超时，单位毫秒
     */
    public AgentServiceImpl(RestTemplate restTemplate, ObjectMapper objectMapper,
                            String baseUrl, long connectTimeout) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
        this.baseUrl = baseUrl;
        this.connectTimeout = connectTimeout;
    }

    /** {@inheritDoc} */
    @Override
    public Result<?> exchange(String path, HttpMethod method, String authorization, Object body) {
        ResponseEntity<String> response = forward(path, method, authorization, toJsonOrNull(body));
        return wrapResult(response.getBody());
    }

    /** {@inheritDoc} */
    @Override
    public void stream(String path, HttpMethod method, String authorization, Object body,
                       Consumer<String> lineConsumer) {
        forwardStream(path, method, authorization, toJsonOrNull(body), lineConsumer);
    }

    /**
     * 将请求对象序列化为 JSON；空对象保持为空，序列化失败时抛出统一业务异常。
     *
     * @param value 待序列化的请求对象，允许为 {@code null}
     * @return JSON 文本；输入为空时返回 {@code null}
     * @throws BizException 对象无法序列化时抛出内部错误
     */
    private String toJsonOrNull(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            log.error("请求数据序列化失败", e);
            throw new BizException(ErrorType.INTERNAL_ERROR, "请求数据序列化失败");
        }
    }

    /**
     * 拼接 Python Agent 的基础地址与相对路径。
     *
     * @param path Agent API 相对路径
     * @return 可供 HTTP 客户端调用的完整地址
     */
    private String agentUrl(String path) {
        return baseUrl + path;
    }

    /**
     * SSE 流式转发专用：不设读超时，思考模型响应可能远超普通接口的 30s 读超时。
     *
     * @return 延迟初始化并在线程间共享的 SSE 客户端，读取无超时限制
     */
    private RestTemplate getStreamRestTemplate() {
        if (streamRestTemplate == null) {
            synchronized (this) {
                if (streamRestTemplate == null) {
                    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
                    factory.setConnectTimeout((int) connectTimeout);
                    factory.setReadTimeout(0);
                    streamRestTemplate = new RestTemplate(factory);
                }
            }
        }
        return streamRestTemplate;
    }

    /**
     * 转发普通 HTTP 请求并将上游 HTTP/网络错误归类为业务异常。
     *
     * @param path Agent API 相对路径
     * @param method HTTP 方法
     * @param authorization 原始 Authorization 请求头，可为空
     * @param body JSON 请求体，可为空
     * @return 上游响应实体
     * @throws BizException 上游返回错误状态或 Agent 不可用时抛出
     */
    private ResponseEntity<String> forward(String path, HttpMethod method,
                                           String authorization, String body) {
        String url = agentUrl(path);
        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setAccept(Collections.singletonList(MediaType.APPLICATION_JSON));

        HttpEntity<String> entity = new HttpEntity<>(body, headers);
        try {
            return restTemplate.exchange(url, method, entity, String.class);
        } catch (HttpStatusCodeException e) {
            log.warn("Agent 请求失败: {} {} -> status={}", method, url, e.getStatusCode().value());
            if (e.getStatusCode().is5xxServerError()) {
                throw new BizException(ErrorType.SERVICE_UNAVAILABLE);
            }
            throw new BizException(mapUpstream4xx(e.getStatusCode().value()));
        } catch (ResourceAccessException e) {
            log.error("Agent 服务连接失败: {}", url, e);
            throw new BizException(ErrorType.SERVICE_UNAVAILABLE, "AI 服务暂不可用");
        }
    }

    /**
     * 以无读超时的客户端转发 SSE，并逐行交给调用方消费。
     *
     * @param path Agent SSE 相对路径
     * @param method HTTP 方法
     * @param authorization 原始 Authorization 请求头，可为空
     * @param body JSON 请求体，可为空
     * @param lineConsumer 每个上游响应行的消费器
     * @throws BizException 上游返回错误状态或 Agent 不可用时抛出
     */
    private void forwardStream(String path, HttpMethod method, String authorization, String body,
                               Consumer<String> lineConsumer) {
        String url = agentUrl(path);
        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setAccept(Collections.singletonList(MediaType.TEXT_EVENT_STREAM));
        String traceId = MDC.get(TraceConstants.MDC_TRACE_ID);
        if (traceId != null) {
            headers.set(TraceConstants.HEADER_X_REQUEST_ID, traceId);
        }

        try {
            getStreamRestTemplate().execute(url, method, request -> {
                request.getHeaders().addAll(headers);
                if (body != null) {
                    request.getBody().write(body.getBytes(StandardCharsets.UTF_8));
                }
            }, response -> {
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(response.getBody(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        lineConsumer.accept(line);
                    }
                }
                return null;
            });
        } catch (HttpStatusCodeException e) {
            log.warn("Agent 流式请求失败: {} {} -> status={}", method, url, e.getStatusCode().value());
            if (e.getStatusCode().is5xxServerError()) {
                throw new BizException(ErrorType.SERVICE_UNAVAILABLE);
            }
            throw new BizException(mapUpstream4xx(e.getStatusCode().value()));
        } catch (ResourceAccessException e) {
            log.error("Agent 流式连接失败: {}", url, e);
            throw new BizException(ErrorType.SERVICE_UNAVAILABLE, "AI 服务暂不可用");
        }
    }

    /**
     * 将 Python Agent 的客户端错误状态映射为 Business 错误类型。
     *
     * @param status 上游 HTTP 状态码
     * @return 对应的统一错误类型，未识别状态映射为 {@link ErrorType#BAD_REQUEST}
     */
    private ErrorType mapUpstream4xx(int status) {
        return switch (status) {
            case 401 -> ErrorType.UNAUTHORIZED;
            case 403 -> ErrorType.FORBIDDEN;
            case 404 -> ErrorType.NOT_FOUND;
            case 429 -> ErrorType.TOO_MANY_REQUESTS;
            default -> ErrorType.BAD_REQUEST;
        };
    }

    /**
     * 将 Agent 的 JSON 响应包装成统一成功结果，无法解析时保留原始正文。
     *
     * @param agentBody Agent 响应正文
     * @return 包含列表、对象或原始字符串的成功结果；空白或 null 正文返回无数据成功结果
     */
    private Result<?> wrapResult(String agentBody) {
        if (agentBody == null || agentBody.isBlank()) {
            return Result.success();
        }
        try {
            if (agentBody.trim().startsWith("[")) {
                List<?> list = objectMapper.readValue(agentBody, List.class);
                return Result.success(list);
            }
            Map<?, ?> map = objectMapper.readValue(agentBody, Map.class);
            return Result.success(map);
        } catch (JsonProcessingException e) {
            log.warn("Agent 响应解析失败，返回原始内容: {}", e.getMessage());
            return Result.success(agentBody);
        }
    }
}
