package top.zhaizz.agent.service;

import org.springframework.http.HttpMethod;
import top.zhaizz.common.result.Result;

import java.util.function.Consumer;

/**
 * Python agent 网关：controller 只关心业务请求与统一响应。
 */
public interface AgentGateway {

    Result<?> exchange(String path, HttpMethod method, String authorization, Object body);

    void stream(String path, HttpMethod method, String authorization, Object body, Consumer<String> lineConsumer);
}
