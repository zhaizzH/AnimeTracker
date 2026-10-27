package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.result.Result;

import static top.zhaizz.agent.constant.AgentApiPaths.*;

import java.io.IOException;
import java.util.Map;

/**
 * Agent 对话控制器（用户端，转发至 Python agent）
 */
@RestController
@RequestMapping("/api/client/agent")
public class ClientAgentController {

    /** 负责转发 Agent 请求的服务 */
    private final AgentService agentService;

    /**
     * 创建用户端 Agent 控制器
     * @param agentService 负责转发 Agent 请求的服务
     */
    public ClientAgentController(final AgentService agentService) {
        this.agentService = agentService;
    }

    /**
     * 健康检查
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游健康状态包装的统一结果
     */
    @GetMapping("/health")
    public Result<?> health(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(CLIENT_HEALTH, HttpMethod.GET, auth, null);
    }

    /**
     * Agent 流式对话（SSE 流式透传，逐行转发 Python agent 响应）
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @param body 向上游透传的请求体
     * @param response 待写入内容的 HTTP 响应；收到上游首行后才提交流式响应头
     * @throws IOException Servlet 响应写入失败时抛出
     */
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public void stream(@RequestHeader("Authorization") String auth, @RequestBody Map<String, Object> body, HttpServletResponse response) throws IOException {
        AgentSseResponseWriter.forward(
                lines -> agentService.stream(CLIENT_STREAM, HttpMethod.POST, auth, body, lines), response);
    }

    /**
     * 重连指定 run 的 SSE 流
     *
     * @param runId 上游 run 标识
     * @param after 已收到的事件数量，缺省为 0
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @param response 待写入内容的 HTTP 响应；收到上游首行后才提交流式响应头
     * @throws IOException Servlet 响应写入失败时抛出
     */
    @GetMapping(value = "/runs/{runId}/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public void runStream(@PathVariable String runId,
                          @RequestParam(defaultValue = "0") int after,
                          @RequestHeader("Authorization") String auth,
                          HttpServletResponse response) throws IOException {
        AgentSseResponseWriter.forward(
                lines -> agentService.streamGet(CLIENT_RUNS + "/" + runId + "/stream", "after=" + after, auth, lines),
                response);
    }

    /**
     * 查询会话当前或最近一条 run
     *
     * @param sessionId 上游会话标识
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游 run 状态包装的统一结果
     */
    @GetMapping("/sessions/{sessionId}/run")
    public Result<?> sessionRun(@PathVariable String sessionId,
                                @RequestHeader("Authorization") String auth) {
        return agentService.exchange(CLIENT_SESSIONS + "/" + sessionId + "/run", HttpMethod.GET, auth, null);
    }

    /**
     * 请求逻辑停止指定 run
     *
     * @param runId 上游 run 标识
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游停止结果包装的统一结果
     */
    @PostMapping("/runs/{runId}/stop")
    public Result<?> stopRun(@PathVariable String runId,
                             @RequestHeader("Authorization") String auth) {
        return agentService.exchange(CLIENT_RUNS + "/" + runId + "/stop", HttpMethod.POST, auth, null);
    }

    /**
     * 获取会话列表
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 当前身份的上游会话列表包装的统一结果
     */
    @GetMapping("/sessions")
    public Result<?> listSessions(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(CLIENT_SESSIONS, HttpMethod.GET, auth, null);
    }

    /**
     * 创建新会话
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @param body 会话创建参数，可为空；空值按空对象转发
     * @return 上游新会话包装的统一结果
     */
    @PostMapping("/sessions")
    public Result<?> createSession(@RequestHeader("Authorization") String auth, @RequestBody(required = false) Map<String, Object> body) {
        return agentService.exchange(CLIENT_SESSIONS, HttpMethod.POST, auth, body != null ? body : Map.of());
    }

    /**
     * 获取会话历史
     *
     * @param sessionId 上游会话标识
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游会话历史包装的统一结果
     */
    @GetMapping("/sessions/{sessionId}/history")
    public Result<?> getHistory(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(CLIENT_SESSIONS + "/" + sessionId + "/history", HttpMethod.GET, auth, null);
    }

    /**
     * 删除会话
     *
     * @param sessionId 上游会话标识
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游删除响应包装的统一结果
     */
    @PostMapping("/sessions/{sessionId}/remove")
    public Result<?> deleteSession(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(CLIENT_SESSIONS + "/" + sessionId, HttpMethod.POST, auth, null);
    }
}
