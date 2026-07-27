package top.zhaizz.client.service;

import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import top.zhaizz.common.result.Result;

import java.util.function.Consumer;

public interface AgentService {

    String toJson(Object value);

    ResponseEntity<String> forward(String path, HttpMethod method, String authorization, String body);

    void forwardStream(String path, HttpMethod method, String authorization, String body, Consumer<String> lineConsumer);

    Result<?> wrapResult(String agentBody);
}
