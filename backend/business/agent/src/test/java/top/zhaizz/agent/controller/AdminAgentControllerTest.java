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

/** 管理员 Agent 代理控制器边界测试 */
class AdminAgentControllerTest {

/** 上游拒绝请求时不得提前获取响应写入器 */
    @Test
    void doesNotCommitWriterBeforeUpstreamError() throws Exception {
        AgentService service = mock(AgentService.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        doThrow(new BizException(ErrorType.UNAUTHORIZED)).when(service)
                .stream(anyString(), eq(HttpMethod.POST), anyString(), any(), any());

        AdminAgentController controller = new AdminAgentController(service);

        assertThrows(BizException.class, () -> controller.stream(
                "Bearer token", Map.of("session_id", "s"), response));
        verify(response, never()).getWriter();
    }

    /** 管理端 GET 重连使用带 chat 前缀的上游路径并透传 after 查询 */
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

        AdminAgentController controller = new AdminAgentController(service);
        controller.runStream("r1", 3, "Bearer token", response);

        verify(service).streamGet(eq("/api/admin/agent/chat/runs/r1/stream"), eq("after=3"), eq("Bearer token"), any());
        verify(response).setContentType("text/event-stream");
        assert output.toString().contains("data: {\"type\":\"answer\"}\n");
    }

    /** 管理端 GET 重连上游失败时不提前获取响应写入器 */
    @Test
    void reconnectDoesNotCommitWriterBeforeUpstreamError() throws Exception {
        AgentService service = mock(AgentService.class);
        HttpServletResponse response = mock(HttpServletResponse.class);
        doThrow(new BizException(ErrorType.NOT_FOUND)).when(service)
                .streamGet(anyString(), anyString(), anyString(), any());

        AdminAgentController controller = new AdminAgentController(service);

        assertThrows(BizException.class, () -> controller.runStream("r1", 0, "Bearer token", response));
        verify(response, never()).getWriter();
    }

    /** 管理端会话 run 查询使用 GET 和 chat 前缀 */
    @Test
    void getsSessionRun() {
        AgentService service = mock(AgentService.class);
        Result<Object> expected = Result.success(Map.of("run_id", "r1", "status", "running"));
        doReturn(expected).when(service).exchange("/api/admin/agent/chat/sessions/s1/run", HttpMethod.GET, "Bearer token", null);

        AdminAgentController controller = new AdminAgentController(service);
        Result<?> actual = controller.sessionRun("s1", "Bearer token");

        assertSame(expected, actual);
        verify(service).exchange("/api/admin/agent/chat/sessions/s1/run", HttpMethod.GET, "Bearer token", null);
    }

    /** 管理端停止 run 使用 POST 和 chat 前缀 */
    @Test
    void stopsRun() {
        AgentService service = mock(AgentService.class);
        Result<Object> expected = Result.success(Map.of("run_id", "r1", "status", "cancelled"));
        doReturn(expected).when(service).exchange("/api/admin/agent/chat/runs/r1/stop", HttpMethod.POST, "Bearer token", null);

        AdminAgentController controller = new AdminAgentController(service);
        Result<?> actual = controller.stopRun("r1", "Bearer token");

        assertSame(expected, actual);
        verify(service).exchange("/api/admin/agent/chat/runs/r1/stop", HttpMethod.POST, "Bearer token", null);
    }
}
