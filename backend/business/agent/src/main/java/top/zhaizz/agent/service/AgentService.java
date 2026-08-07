package top.zhaizz.agent.service;

import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import top.zhaizz.common.result.Result;

import java.util.function.Consumer;

/**
 * Agent 服务：统一封装对 Python agent 的 HTTP 转发
 */
public interface AgentService {

    /** 对象转 JSON 字符串，序列化失败抛业务异常 */
    String toJson(Object value);

    /** 按 path 转发请求到 Python agent，返回原始响应体 */
    ResponseEntity<String> forward(String path, HttpMethod method, String authorization, String body);

    /** SSE 流式转发，按行回调透传 Python agent 响应 */
    void forwardStream(String path, HttpMethod method, String authorization, String body, Consumer<String> lineConsumer);

    /** 解析 Python agent 响应为统一 Result，解析失败时原样透传 */
    Result<?> wrapResult(String agentBody);
}
