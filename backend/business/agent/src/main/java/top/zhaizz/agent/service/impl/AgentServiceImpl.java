package top.zhaizz.agent.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.constant.TraceConstants;
import top.zhaizz.common.config.AgentProperties;
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
 * AgentService 实现：转发请求到 Python agent，统一归类上游错误
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AgentServiceImpl implements AgentService {

    private final RestTemplate restTemplate;
    private final AgentProperties agentProperties;
    private final ObjectMapper objectMapper;
    // SSE 流式转发专用模板（懒加载，双检锁保证单例）
    private volatile RestTemplate streamRestTemplate;

    @Override
    public String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            log.error("请求数据序列化失败", e);
            throw new BizException(ErrorType.INTERNAL_ERROR, "请求数据序列化失败");
        }
    }

    private String agentUrl(String path) {
        return agentProperties.getBaseUrl() + path;
    }

    /** SSE 流式转发专用：不设读超时，思考模型响应可能远超普通接口的 30s 读超时。 */
    private RestTemplate getStreamRestTemplate() {
        if (streamRestTemplate == null) {
            synchronized (this) {
                if (streamRestTemplate == null) {
                    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
                    factory.setConnectTimeout((int) agentProperties.getConnectTimeout());
                    factory.setReadTimeout(0);
                    streamRestTemplate = new RestTemplate(factory);
                }
            }
        }
        return streamRestTemplate;
    }

    @Override
    public ResponseEntity<String> forward(String path, HttpMethod method,
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
            // 日志不记录上游响应体（隐私红线）；错误体不得直接返回访客
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

    /** 上游 4xx 尽可能保留 401/403/404 等语义，其余归为 400 */
    private ErrorType mapUpstream4xx(int status) {
        return switch (status) {
            case 401 -> ErrorType.UNAUTHORIZED;
            case 403 -> ErrorType.FORBIDDEN;
            case 404 -> ErrorType.NOT_FOUND;
            case 429 -> ErrorType.TOO_MANY_REQUESTS;
            default -> ErrorType.BAD_REQUEST;
        };
    }

    @Override
    public void forwardStream(String path, HttpMethod method, String authorization, String body,
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
            // 上游非 2xx（如请求体校验失败 422）：流未开始则归类到统一 Result，不泄露错误体
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

    @Override
    public Result<?> wrapResult(String agentBody) {
        try {
            // Agent 响应可能是列表或对象，解析失败时回退原文透传
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
