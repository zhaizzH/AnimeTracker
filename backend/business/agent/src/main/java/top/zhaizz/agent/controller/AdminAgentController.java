package top.zhaizz.agent.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.result.Result;

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
        return agentService.wrapResult(agentService.forward("/api/admin/agent/prompts", HttpMethod.GET, auth, null).getBody());
    }

    /**
     * 提示词详情
     */
    @GetMapping("/prompts/{key}")
    public Result<?> getPrompt(@PathVariable String key, @RequestHeader("Authorization") String auth) {
        return agentService.wrapResult(agentService.forward("/api/admin/agent/prompts/" + key, HttpMethod.GET, auth, null).getBody());
    }

    /**
     * 更新提示词
     */
    @PostMapping("/prompts/{key}/update")
    public Result<?> updatePrompt(@PathVariable String key, @RequestBody Map<String, Object> body,
                                  @RequestHeader("Authorization") String auth) {
        return agentService.wrapResult(agentService.forward(
                "/api/admin/agent/prompts/" + key + "/update", HttpMethod.POST, auth, agentService.toJson(body)).getBody());
    }

    /**
     * 重置提示词为默认
     */
    @PostMapping("/prompts/{key}/reset")
    public Result<?> resetPrompt(@PathVariable String key, @RequestHeader("Authorization") String auth) {
        return agentService.wrapResult(agentService.forward(
                "/api/admin/agent/prompts/" + key + "/reset", HttpMethod.POST, auth, null).getBody());
    }

    /**
     * 读取模型配置
     */
    @GetMapping("/config")
    public Result<?> getConfig(@RequestHeader("Authorization") String auth) {
        return agentService.wrapResult(agentService.forward("/api/admin/agent/config", HttpMethod.GET, auth, null).getBody());
    }

    /**
     * 更新模型配置
     */
    @PostMapping("/config/update")
    public Result<?> updateConfig(@RequestBody Map<String, Object> body, @RequestHeader("Authorization") String auth) {
        return agentService.wrapResult(agentService.forward(
                "/api/admin/agent/config/update", HttpMethod.POST, auth, agentService.toJson(body)).getBody());
    }
}
