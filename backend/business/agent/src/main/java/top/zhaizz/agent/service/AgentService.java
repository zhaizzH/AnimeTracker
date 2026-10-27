package top.zhaizz.agent.service;

import org.springframework.http.HttpMethod;
import top.zhaizz.common.result.Result;

import java.util.function.Consumer;

/**
 * Python agent 服务：controller 只关心业务请求与统一响应
 */
public interface AgentService {

    /**
     * 转发普通 HTTP 请求并将 Agent 响应包装为统一结果
     *
     * @param path Agent API 相对路径
     * @param method HTTP 方法
     * @param authorization 原始授权请求头，可为空
     * @param body 请求体，可为空
     * @return 包含上游 JSON 对象、数组或原始正文的成功结果；空白正文返回无数据成功结果
     * @throws top.zhaizz.common.exception.BizException 序列化失败时为内部错误；上游 5xx 或连接失败时为服务不可用；
     *         上游 401/403/404/429 保留对应类型，其他 4xx 为请求错误
     */
    Result<?> exchange(String path, HttpMethod method, String authorization, Object body);

    /**
     * 转发流式 HTTP 请求并逐行消费 Agent 响应
     *
     * @param path Agent SSE API 相对路径
     * @param method HTTP 方法
     * @param authorization 原始授权请求头，可为空
     * @param body 请求体，可为空
     * @param lineConsumer 每行响应内容的消费器，包含空行；回调异常向调用方传播
     * @throws top.zhaizz.common.exception.BizException 请求序列化失败、上游错误状态或连接失败时抛出
     */
    void stream(String path, HttpMethod method, String authorization, Object body, Consumer<String> lineConsumer);

    /**
     * 以 GET 转发流式 HTTP 请求（run 重连），查询参数独立于路径传递
     * <p>
     * 与 {@link #stream} 的区别：不写请求体、不声明 JSON Content-Type，
     * 上游 409 时抛出携带结构化 detail 的 {@code BizException}
     *
     * @param path Agent SSE API 相对路径，不含查询串
     * @param query 已编码的查询串（如 {@code after=0}），可为空
     * @param authorization 原始授权请求头，可为空
     * @param lineConsumer 每行响应内容的消费器，包含空行；回调异常向调用方传播
     * @throws top.zhaizz.common.exception.BizException 上游错误状态或连接失败时抛出；409 时 data 为上游 detail 对象
     */
    void streamGet(String path, String query, String authorization, Consumer<String> lineConsumer);
}
