package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.result.Result;

import static top.zhaizz.common.constant.AgentApiPaths.*;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.Map;

/**
 * Agent 配置管理控制器（管理端，转发至 Python agent）
 */
@RestController
@RequestMapping("/api/admin/agent")
@RequiredArgsConstructor
public class AdminAgentController {

    private final AgentService agentService;

    /**
     * 提示词列表
     */
    @GetMapping("/prompts")
    public Result<?> listPrompts(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS, HttpMethod.GET, auth, null);
    }

    /**
     * 提示词详情
     */
    @GetMapping("/prompts/{key}")
    public Result<?> getPrompt(@PathVariable String key, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS + "/" + key, HttpMethod.GET, auth, null);
    }

    /**
     * 更新提示词
     */
    @OperationLog(action = OperationLogConstants.ACTION_PROMPT_UPDATE, module = OperationLogConstants.MODULE_AGENT)
    @PostMapping("/prompts/{key}/update")
    public Result<?> updatePrompt(@PathVariable String key, @RequestBody Map<String, Object> body,
                                  @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS + "/" + key + "/update", HttpMethod.POST, auth, body);
    }

    /**
     * 重置提示词为默认
     */
    @OperationLog(action = OperationLogConstants.ACTION_PROMPT_RESET, module = OperationLogConstants.MODULE_AGENT)
    @PostMapping("/prompts/{key}/reset")
    public Result<?> resetPrompt(@PathVariable String key, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS + "/" + key + "/reset", HttpMethod.POST, auth, null);
    }

    /**
     * 读取模型配置
     */
    @GetMapping("/config")
    public Result<?> getConfig(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CONFIG, HttpMethod.GET, auth, null);
    }

    /**
     * 更新模型配置
     */
    @OperationLog(action = OperationLogConstants.ACTION_CONFIG_UPDATE, module = OperationLogConstants.MODULE_AGENT)
    @PostMapping("/config/update")
    public Result<?> updateConfig(@RequestBody Map<String, Object> body, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CONFIG + "/update", HttpMethod.POST, auth, body);
    }

    /**
     * 管理端 Agent 流式对话（SSE 流式透传，逐行转发 Python agent 响应）
     */
    @PostMapping(value = "/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public void stream(@RequestHeader("Authorization") String auth, @RequestBody Map<String, Object> body, HttpServletResponse response) throws IOException {
        response.setContentType(MediaType.TEXT_EVENT_STREAM_VALUE);
        response.setCharacterEncoding("UTF-8");
        PrintWriter writer = response.getWriter();
        agentService.stream(ADMIN_CHAT_STREAM, HttpMethod.POST, auth, body, line -> {
            writer.write(line + "\n");
            writer.flush();
        });
        writer.close();
    }

    /**
     * 获取管理端会话列表
     */
    @GetMapping("/chat/sessions")
    public Result<?> listSessions(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS, HttpMethod.GET, auth, null);
    }

    /**
     * 创建管理端会话
     */
    @PostMapping("/chat/sessions")
    public Result<?> createSession(@RequestHeader("Authorization") String auth, @RequestBody(required = false) Map<String, Object> body) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS, HttpMethod.POST, auth, body != null ? body : Map.of());
    }

    /**
     * 获取管理端会话历史
     */
    @GetMapping("/chat/sessions/{sessionId}/history")
    public Result<?> getHistory(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS + "/" + sessionId + "/history", HttpMethod.GET, auth, null);
    }

    /**
     * 删除管理端会话
     */
    @PostMapping("/chat/sessions/{sessionId}/remove")
    public Result<?> deleteSession(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS + "/" + sessionId, HttpMethod.POST, auth, null);
    }
}
