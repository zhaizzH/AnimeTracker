package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.Result;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Map;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/** 用户 Agent 代理控制器边界测试 */
class ClientAgentControllerTest {

/** 上游拒绝请求时不得提前获取响应写入器 */
    @Test
    void doesNotCommitWriterBeforeUpstreamError() throws Exception {
        AgentService service = mock(AgentService.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        doThrow(new BizException(ErrorType.UNAUTHORIZED)).when(service)
                .stream(anyString(), eq(HttpMethod.POST), anyString(), any(), any());

        ClientAgentController controller = new ClientAgentController(service);

        assertThrows(BizException.class, () -> controller.stream(
                "Bearer token", Map.of("session_id", "s"), response));
        verify(response, never()).getWriter();
    }

/** 收到首条成功事件后才打开写入器并声明 SSE 内容类型 */
    @Test
    @SuppressWarnings("unchecked")
    void opensWriterOnFirstSuccessfulLine() throws Exception {
        AgentService service = mock(AgentService.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        StringWriter output = new StringWriter();
        when(response.getWriter()).thenReturn(new PrintWriter(output));
        doAnswer(invocation -> {
            Consumer<String> consumer = invocation.getArgument(4);
            consumer.accept("data: {\"type\":\"answer\"}");
            return null;
        }).when(service).stream(anyString(), eq(HttpMethod.POST), anyString(), any(), any());

        ClientAgentController controller = new ClientAgentController(service);
        controller.stream("Bearer token", Map.of("session_id", "s"), response);

        verify(response).getWriter();
        verify(response).setContentType("text/event-stream");
        assert output.toString().contains("data: {\"type\":\"answer\"}\n");
    }

    /** GET 重连把 after 作为查询参数传给上游，并逐行写出 SSE 响应 */
    @Test
    @SuppressWarnings("unchecked")
    void reconnectsRunWithAfterQuery() throws Exception {
        AgentService service = mock(AgentService.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        StringWriter output = new StringWriter();
        when(response.getWriter()).thenReturn(new PrintWriter(output));
        doAnswer(invocation -> {
            Consumer<String> consumer = invocation.getArgument(3);
            consumer.accept("data: {\"type\":\"answer\"}");
            return null;
        }).when(service).streamGet(anyString(), anyString(), anyString(), any());

        ClientAgentController controller = new ClientAgentController(service);
        controller.runStream("r1", 3, "Bearer token", response);

        verify(service).streamGet(eq("/api/client/agent/runs/r1/stream"), eq("after=3"), eq("Bearer token"), any());
        verify(response).setContentType("text/event-stream");
        assert output.toString().contains("data: {\"type\":\"answer\"}\n");
    }

    /** GET 重连的上游错误不得因提前提交 SSE 响应而变成成功响应 */
    @Test
    void reconnectDoesNotCommitWriterBeforeUpstreamError() throws Exception {
        AgentService service = mock(AgentService.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        doThrow(new BizException(ErrorType.NOT_FOUND)).when(service)
                .streamGet(anyString(), anyString(), anyString(), any());

        ClientAgentController controller = new ClientAgentController(service);

        assertThrows(BizException.class, () -> controller.runStream("r1", 0, "Bearer token", response));
        verify(response, never()).getWriter();
    }

    /** 会话 run 查询使用 GET 并保留统一结果信封 */
    @Test
    void getsSessionRun() {
        AgentService service = mock(AgentService.class);
        Result<Object> expected = Result.success(Map.of("run_id", "r1", "status", "running"));
        doReturn(expected).when(service).exchange("/api/client/agent/sessions/s1/run", HttpMethod.GET, "Bearer token", null);

        ClientAgentController controller = new ClientAgentController(service);
        Result<?> actual = controller.sessionRun("s1", "Bearer token");

        assertSame(expected, actual);
        verify(service).exchange("/api/client/agent/sessions/s1/run", HttpMethod.GET, "Bearer token", null);
    }

    /** 停止 run 使用 POST，路径中的 runId 原样传给上游 */
    @Test
    void stopsRun() {
        AgentService service = mock(AgentService.class);
        Result<Object> expected = Result.success(Map.of("run_id", "r1", "status", "cancelled"));
        doReturn(expected).when(service).exchange("/api/client/agent/runs/r1/stop", HttpMethod.POST, "Bearer token", null);

        ClientAgentController controller = new ClientAgentController(service);
        Result<?> actual = controller.stopRun("r1", "Bearer token");

        assertSame(expected, actual);
        verify(service).exchange("/api/client/agent/runs/r1/stop", HttpMethod.POST, "Bearer token", null);
    }
}
