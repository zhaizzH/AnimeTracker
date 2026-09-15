package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.result.Result;

import static top.zhaizz.agent.constant.AgentApiPaths.*;

import java.io.IOException;
import java.io.PrintWriter;
import java.io.UncheckedIOException;
import java.util.Map;

/**
 * Agent 对话控制器（用户端，转发至 Python agent）
 */
@RestController
@RequestMapping("/api/client/agent")
@RequiredArgsConstructor
public class ClientAgentController {

    /** 负责转发 Agent 请求的服务 */
    private final AgentService agentService;

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
        // Do not obtain the writer before the upstream call.  RestTemplate
        // maps upstream 4xx responses to BizException; committing an SSE
        // response first would turn those errors into a misleading 401/200.
        final PrintWriter[] writerRef = new PrintWriter[1];

        agentService.stream(CLIENT_STREAM, HttpMethod.POST, auth, body, line -> {
            try {
                if (writerRef[0] == null) {
                    response.setContentType(MediaType.TEXT_EVENT_STREAM_VALUE);
                    response.setCharacterEncoding("UTF-8");
                    writerRef[0] = response.getWriter();
                }
                writerRef[0].write(line + "\n");
                writerRef[0].flush();
            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
        });

        if (writerRef[0] != null) {
            writerRef[0].close();
        }
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
