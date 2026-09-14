package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Map;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/** 用户 Agent 代理控制器边界测试。 */
class ClientAgentControllerTest {

/** 上游拒绝请求时不得提前获取响应写入器。 */
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

/** 收到首条成功事件后才打开写入器并声明 SSE 内容类型。 */
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
}
