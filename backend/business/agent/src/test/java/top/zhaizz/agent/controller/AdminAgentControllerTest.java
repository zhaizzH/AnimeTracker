package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class AdminAgentControllerTest {

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
}
