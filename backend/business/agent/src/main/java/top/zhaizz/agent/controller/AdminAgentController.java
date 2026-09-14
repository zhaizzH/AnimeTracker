package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.log.constant.OperationLogConstants;
import top.zhaizz.log.annotation.OperationLog;
import top.zhaizz.common.result.Result;

import static top.zhaizz.agent.constant.AgentApiPaths.*;

import java.io.IOException;
import java.io.PrintWriter;
import java.io.UncheckedIOException;
import java.util.Map;

/**
 * Agent 配置管理控制器（管理端，转发至 Python agent）。
 */
@RestController
@RequestMapping("/api/admin/agent")
@RequiredArgsConstructor
public class AdminAgentController {

    /** 负责转发 Agent 请求的服务。 */
    private final AgentService agentService;

    /**
     * 提示词列表。
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游提示词列表包装的统一结果
     */
    @GetMapping("/prompts")
    public Result<?> listPrompts(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS, HttpMethod.GET, auth, null);
    }

    /**
     * 提示词详情。
     *
     * @param key 上游提示词配置键
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游提示词内容包装的统一结果
     */
    @GetMapping("/prompts/{key}")
    public Result<?> getPrompt(@PathVariable String key, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS + "/" + key, HttpMethod.GET, auth, null);
    }

    /**
     * 更新提示词。
     *
     * @param key 上游提示词配置键
     * @param body 向上游透传的请求体
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游提示词更新响应包装的统一结果
     */
    @OperationLog(action = OperationLogConstants.ACTION_PROMPT_UPDATE, module = OperationLogConstants.MODULE_AGENT)
    @PostMapping("/prompts/{key}/update")
    public Result<?> updatePrompt(@PathVariable String key, @RequestBody Map<String, Object> body,
                                  @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS + "/" + key + "/update", HttpMethod.POST, auth, body);
    }

    /**
     * 重置提示词为默认。
     *
     * @param key 上游提示词配置键
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游提示词重置响应包装的统一结果
     */
    @OperationLog(action = OperationLogConstants.ACTION_PROMPT_RESET, module = OperationLogConstants.MODULE_AGENT)
    @PostMapping("/prompts/{key}/reset")
    public Result<?> resetPrompt(@PathVariable String key, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_PROMPTS + "/" + key + "/reset", HttpMethod.POST, auth, null);
    }

    /**
     * 读取模型配置。
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游模型配置包装的统一结果
     */
    @GetMapping("/config")
    public Result<?> getConfig(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CONFIG, HttpMethod.GET, auth, null);
    }

    /**
     * 更新模型配置。
     *
     * @param body 向上游透传的请求体
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游配置更新响应包装的统一结果
     */
    @OperationLog(action = OperationLogConstants.ACTION_CONFIG_UPDATE, module = OperationLogConstants.MODULE_AGENT)
    @PostMapping("/config/update")
    public Result<?> updateConfig(@RequestBody Map<String, Object> body, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CONFIG + "/update", HttpMethod.POST, auth, body);
    }

    /**
     * 管理端 Agent 流式对话（SSE 流式透传，逐行转发 Python agent 响应）。
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @param body 向上游透传的请求体
     * @param response 待写入内容的 HTTP 响应；收到上游首行后才提交流式响应头
     * @throws IOException Servlet 响应写入失败时抛出
     */
    @PostMapping(value = "/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public void stream(@RequestHeader("Authorization") String auth, @RequestBody Map<String, Object> body, HttpServletResponse response) throws IOException {
        final PrintWriter[] writerRef = new PrintWriter[1];
        agentService.stream(ADMIN_CHAT_STREAM, HttpMethod.POST, auth, body, line -> {
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
     * 获取管理端会话列表。
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 当前身份的上游会话列表包装的统一结果
     */
    @GetMapping("/chat/sessions")
    public Result<?> listSessions(@RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS, HttpMethod.GET, auth, null);
    }

    /**
     * 创建管理端会话。
     *
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @param body 会话创建参数，可为空；空值按空对象转发
     * @return 上游新会话包装的统一结果
     */
    @PostMapping("/chat/sessions")
    public Result<?> createSession(@RequestHeader("Authorization") String auth, @RequestBody(required = false) Map<String, Object> body) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS, HttpMethod.POST, auth, body != null ? body : Map.of());
    }

    /**
     * 获取管理端会话历史。
     *
     * @param sessionId 上游会话标识
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游会话历史包装的统一结果
     */
    @GetMapping("/chat/sessions/{sessionId}/history")
    public Result<?> getHistory(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS + "/" + sessionId + "/history", HttpMethod.GET, auth, null);
    }

    /**
     * 删除管理端会话。
     *
     * @param sessionId 上游会话标识
     * @param auth 透传给 Python Agent 的 Authorization 请求头
     * @return 上游删除响应包装的统一结果
     */
    @PostMapping("/chat/sessions/{sessionId}/remove")
    public Result<?> deleteSession(@PathVariable String sessionId, @RequestHeader("Authorization") String auth) {
        return agentService.exchange(ADMIN_CHAT_SESSIONS + "/" + sessionId, HttpMethod.POST, auth, null);
    }
}
