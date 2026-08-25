package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.result.Result;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Map;
import java.util.function.Consumer;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoMoreInteractions;

class AgentControllerServiceTest {

    @Test
    void clientControllerDelegatesExchangeToService() {
        AgentService service = mock(AgentService.class);
        ClientAgentController controller = new ClientAgentController(service);

        controller.health("Bearer token");

        verify(service).exchange("/api/client/agent/health", HttpMethod.GET, "Bearer token", null);
        verifyNoMoreInteractions(service);
    }

    @Test
    void clientControllerDelegatesStreamBodyToServiceAndFlushesEachLine() throws Exception {
        AgentService service = mock(AgentService.class);
        ClientAgentController controller = new ClientAgentController(service);
        HttpServletResponse response = mock(HttpServletResponse.class);
        StringWriter buffer = new StringWriter();
        PrintWriter writer = new PrintWriter(buffer);
        doAnswer(invocation -> {
            Consumer<String> consumer = invocation.getArgument(4);
            consumer.accept("data: one");
            consumer.accept("");
            return null;
        }).when(service).stream(eq("/api/client/agent/stream"), eq(HttpMethod.POST), eq("Bearer token"),
                eq(Map.of("content", "hi")), any());
        org.mockito.Mockito.when(response.getWriter()).thenReturn(writer);

        controller.stream("Bearer token", Map.of("content", "hi"), response);

        assertThat(buffer.toString()).isEqualTo("data: one\n\n");
        verify(response).setContentType("text/event-stream");
        verify(response).setCharacterEncoding("UTF-8");
        verify(service).stream(eq("/api/client/agent/stream"), eq(HttpMethod.POST), eq("Bearer token"),
                eq(Map.of("content", "hi")), any());
        verifyNoMoreInteractions(service);
    }

    @Test
    void adminControllerDelegatesExchangeToService() {
        AgentService service = mock(AgentService.class);
        AdminAgentController controller = new AdminAgentController(service);
        Result<?> expected = Result.success(Map.of("key", "value"));
        doReturn(expected).when(service).exchange("/api/admin/agent/prompts/k/update",
                HttpMethod.POST, "Bearer token", Map.of("value", "v"));

        Result<?> result = controller.updatePrompt("k", Map.of("value", "v"), "Bearer token");

        assertThat(result).isSameAs(expected);
        verify(service).exchange("/api/admin/agent/prompts/k/update",
                HttpMethod.POST, "Bearer token", Map.of("value", "v"));
        verifyNoMoreInteractions(service);
    }

    @Test
    void adminControllerDelegatesStreamBodyToServiceAndFlushesEachLine() throws Exception {
        AgentService service = mock(AgentService.class);
        AdminAgentController controller = new AdminAgentController(service);
        HttpServletResponse response = mock(HttpServletResponse.class);
        StringWriter buffer = new StringWriter();
        PrintWriter writer = new PrintWriter(buffer);
        doAnswer(invocation -> {
            Consumer<String> consumer = invocation.getArgument(4);
            consumer.accept("data: admin");
            consumer.accept("");
            return null;
        }).when(service).stream(eq("/api/admin/agent/chat/stream"), eq(HttpMethod.POST), eq("Bearer token"),
                eq(Map.of("content", "hi")), any());
        org.mockito.Mockito.when(response.getWriter()).thenReturn(writer);

        controller.stream("Bearer token", Map.of("content", "hi"), response);

        assertThat(buffer.toString()).isEqualTo("data: admin\n\n");
        verify(response).setContentType("text/event-stream");
        verify(response).setCharacterEncoding("UTF-8");
        verify(service).stream(eq("/api/admin/agent/chat/stream"), eq(HttpMethod.POST), eq("Bearer token"),
                eq(Map.of("content", "hi")), any());
        verifyNoMoreInteractions(service);
    }
}
