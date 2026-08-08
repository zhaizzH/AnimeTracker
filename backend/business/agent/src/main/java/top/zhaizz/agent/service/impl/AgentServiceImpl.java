package top.zhaizz.agent.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.ErrorType;
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
                    factory.setConnectTimeout(10_000);
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
            String errBody = e.getResponseBodyAsString();
            String detail = errBody == null || errBody.isEmpty() ? "无响应" : errBody;
            // 5xx 归为服务端错误，4xx 归为客户端请求错误
            throw new BizException(e.getStatusCode().is5xxServerError()
                            ? ErrorType.INTERNAL_ERROR : ErrorType.BAD_REQUEST,
                    "Agent 请求失败: " + detail);
        } catch (ResourceAccessException e) {
            log.error("Agent 服务连接失败: {}", url, e);
            throw new BizException(ErrorType.INTERNAL_ERROR, "Agent 服务连接失败");
        }
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
