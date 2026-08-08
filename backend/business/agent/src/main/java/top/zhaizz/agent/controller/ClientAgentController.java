package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.result.Result;

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

    private final AgentService agentService;

    /**
     * 健康检查
     */
    @GetMapping("/health")
    public Result<?> health(@RequestHeader("Authorization") String auth) {
        ResponseEntity<String> resp = agentService.forward("/api/client/agent/health", HttpMethod.GET, auth, null);
        return agentService.wrapResult(resp.getBody());
    }

    /**
     * Agent 流式对话（SSE 流式透传，逐行转发 Python agent 响应）
     */
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public void stream(@RequestHeader("Authorization") String auth, @RequestBody Map<String, Object> body, HttpServletResponse response) throws IOException {
        String jsonBody = agentService.toJson(body);

        response.setContentType(MediaType.TEXT_EVENT_STREAM_VALUE);
        response.setCharacterEncoding("UTF-8");
        PrintWriter writer = response.getWriter();

        agentService.forwardStream("/api/client/agent/stream", HttpMethod.POST, auth, jsonBody, line -> {
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
        ResponseEntity<String> resp = agentService.forward("/api/client/agent/sessions", HttpMethod.GET, auth, null);
        return agentService.wrapResult(resp.getBody());
    }

    /**
     * 创建新会话
     */
    @PostMapping("/sessions")
    public Result<?> createSession(@RequestHeader("Authorization") String auth, @RequestBody(required = false) Map<String, Object> body) {
        String jsonBody = agentService.toJson(body != null ? body : Map.of());
        ResponseEntity<String> resp = agentService.forward("/api/client/agent/sessions", HttpMethod.POST, auth, jsonBody);
        return agentService.wrapResult(resp.getBody());
    }

    /**
     * 获取会话历史
     */
    @GetMapping("/sessions/{sessionId}/history")
    public Result<?> getHistory(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        ResponseEntity<String> resp = agentService.forward("/api/client/agent/sessions/" + sessionId + "/history", HttpMethod.GET, auth, null);
        return agentService.wrapResult(resp.getBody());
    }

    /**
     * 删除会话
     */
    @PostMapping("/sessions/{sessionId}/remove")
    public Result<?> deleteSession(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        ResponseEntity<String> resp = agentService.forward("/api/client/agent/sessions/" + sessionId, HttpMethod.POST, auth, null);
        return agentService.wrapResult(resp.getBody());
    }
}
