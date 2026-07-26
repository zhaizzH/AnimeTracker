package top.zhaizz.client.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.result.Result;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.Map;
import java.util.function.Consumer;

@Slf4j
@Service
@RequiredArgsConstructor
public class AgentService {

    private final RestTemplate restTemplate;
    private final AgentProperties agentProperties;
    private final ObjectMapper objectMapper;

    public String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("JSON serialization failed", e);
        }
    }

    private String agentUrl(String path) {
        return agentProperties.getBaseUrl() + "/api/chat" + path;
    }

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
        return restTemplate.exchange(url, method, entity, String.class);
    }

    public void forwardStream(String path, HttpMethod method, String authorization, String body,
                              Consumer<String> lineConsumer) {
        String url = agentUrl(path);
        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.isEmpty()) {
            headers.set(HttpHeaders.AUTHORIZATION, authorization);
        }
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setAccept(Collections.singletonList(MediaType.TEXT_EVENT_STREAM));

        restTemplate.execute(url, method, request -> {
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

    public Result<?> wrapResult(String agentBody) {
        try {
            Map<?, ?> map = objectMapper.readValue(agentBody, Map.class);
            return Result.success(map);
        } catch (JsonProcessingException e) {
            log.warn("Agent response parse failed, return raw: {}", e.getMessage());
            return Result.success(agentBody);
        }
    }
}
