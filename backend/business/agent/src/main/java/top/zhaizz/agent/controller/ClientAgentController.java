package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.agent.service.AgentGateway;
import top.zhaizz.common.result.Result;

import static top.zhaizz.common.constant.AgentApiPaths.*;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.Map;

/**
 * Agent 对话控制器（用户端，转发至 Python agent）
 */
@RestController
@RequestMapping("/api/client/agent")
@RequiredArgsConstructor
public class ClientAgentController {

    private final AgentGateway agentGateway;

    /**
     * 健康检查
     */
    @GetMapping("/health")
    public Result<?> health(@RequestHeader("Authorization") String auth) {
        return agentGateway.exchange(CLIENT_HEALTH, HttpMethod.GET, auth, null);
    }

    /**
     * Agent 流式对话（SSE 流式透传，逐行转发 Python agent 响应）
     */
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public void stream(@RequestHeader("Authorization") String auth, @RequestBody Map<String, Object> body, HttpServletResponse response) throws IOException {
        response.setContentType(MediaType.TEXT_EVENT_STREAM_VALUE);
        response.setCharacterEncoding("UTF-8");
        PrintWriter writer = response.getWriter();

        agentGateway.stream(CLIENT_STREAM, HttpMethod.POST, auth, body, line -> {
            writer.write(line + "\n");
            writer.flush();
        });

        writer.close();
    }

    /**
     * 获取会话列表
     */
    @GetMapping("/sessions")
    public Result<?> listSessions(@RequestHeader("Authorization") String auth) {
        return agentGateway.exchange(CLIENT_SESSIONS, HttpMethod.GET, auth, null);
    }

    /**
     * 创建新会话
     */
    @PostMapping("/sessions")
    public Result<?> createSession(@RequestHeader("Authorization") String auth, @RequestBody(required = false) Map<String, Object> body) {
        return agentGateway.exchange(CLIENT_SESSIONS, HttpMethod.POST, auth, body != null ? body : Map.of());
    }

    /**
     * 获取会话历史
     */
    @GetMapping("/sessions/{sessionId}/history")
    public Result<?> getHistory(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentGateway.exchange(CLIENT_SESSIONS + "/" + sessionId + "/history", HttpMethod.GET, auth, null);
    }

    /**
     * 删除会话
     */
    @PostMapping("/sessions/{sessionId}/remove")
    public Result<?> deleteSession(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentGateway.exchange(CLIENT_SESSIONS + "/" + sessionId, HttpMethod.POST, auth, null);
    }
}
