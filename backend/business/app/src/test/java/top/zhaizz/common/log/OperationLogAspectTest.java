package top.zhaizz.common.log;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.aop.aspectj.annotation.AspectJProxyFactory;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.security.authentication.TestingAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import top.zhaizz.common.mapper.OperationLogMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class OperationLogAspectTest {

    private OperationLogMapper mapper;
    private Target target;

    @BeforeEach
    void setUp() {
        mapper = mock(OperationLogMapper.class);
        OperationLogAspect aspect = new OperationLogAspect(mapper, new ObjectMapper());
        AspectJProxyFactory factory = new AspectJProxyFactory(new Target());
        factory.addAspect(aspect);
        target = factory.getProxy();
        SecurityContextHolder.getContext().setAuthentication(new TestingAuthenticationToken(1L, null));
        RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(
                new MockHttpServletRequest("POST", "/api/client/auth/login")));
    }

    @AfterEach
    void tearDown() {
        SecurityContextHolder.clearContext();
        RequestContextHolder.resetRequestAttributes();
    }

    @Test
    void logsSuccessWithMaskedParams() {
        target.login(new LoginArg("bob", "secret123"));
        ArgumentCaptor<top.zhaizz.pojo.entity.OperationLog> cap = ArgumentCaptor.forClass(top.zhaizz.pojo.entity.OperationLog.class);
        verify(mapper).insert(cap.capture());
        top.zhaizz.pojo.entity.OperationLog e = cap.getValue();
        assertThat(e.getAction()).isEqualTo("LOGIN");
        assertThat(e.getStatus()).isZero();
        assertThat(e.getUserId()).isEqualTo(1L);
        assertThat(e.getUsername()).isEqualTo("bob");
        assertThat(e.getParams()).doesNotContain("secret123");
        assertThat(e.getPath()).isEqualTo("/api/client/auth/login");
    }

    @Test
    void logsFailureWhenTargetThrows() {
        try {
            target.fail();
        } catch (RuntimeException ignored) {
        }
        ArgumentCaptor<top.zhaizz.pojo.entity.OperationLog> cap = ArgumentCaptor.forClass(top.zhaizz.pojo.entity.OperationLog.class);
        verify(mapper).insert(cap.capture());
        assertThat(cap.getValue().getStatus()).isEqualTo(1);
        assertThat(cap.getValue().getErrorMsg()).contains("boom");
    }

    @Test
    void loggingFailureDoesNotBreakBusiness() {
        doThrow(new RuntimeException("db down")).when(mapper).insert(any());
        target.login(new LoginArg("bob", "secret123")); // 不抛异常
    }

    static class Target {
        @top.zhaizz.common.log.OperationLog(action = "LOGIN", module = "AUTH")
        public void login(LoginArg arg) {
        }

        @top.zhaizz.common.log.OperationLog(action = "SUBJECT_CREATE", module = "SUBJECT")
        public void fail() {
            throw new IllegalStateException("boom");
        }
    }

    static class LoginArg {
        private final String username;
        private final String password;

        LoginArg(String username, String password) {
            this.username = username;
            this.password = password;
        }

        public String getUsername() {
            return username;
        }

        public String getPassword() {
            return password;
        }
    }
}
