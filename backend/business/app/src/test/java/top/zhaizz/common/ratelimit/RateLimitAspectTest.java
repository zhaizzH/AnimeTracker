package top.zhaizz.common.ratelimit;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.aop.aspectj.annotation.AspectJProxyFactory;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import top.zhaizz.common.exception.BizException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.startsWith;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RateLimitAspectTest {

    private RateLimiter limiter;
    private Target target;

    @BeforeEach
    void setUp() {
        limiter = mock(RateLimiter.class);
        when(limiter.allowOrCount(anyString(), anyInt(), anyInt())).thenReturn(true);
        RateLimitAspect aspect = new RateLimitAspect(limiter);
        AspectJProxyFactory factory = new AspectJProxyFactory(new Target());
        factory.addAspect(aspect);
        target = factory.getProxy();
        RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(
                new MockHttpServletRequest("POST", "/api/user/auth/resend-code")));
    }

    @AfterEach
    void tearDown() {
        RequestContextHolder.resetRequestAttributes();
    }

    @Test
    void proceedsWhenUnderLimit() {
        target.resendCode(new EmailArg("a@b.com"));
        assertThat(target.isCalled()).isTrue();
    }

    @Test
    void throwsBizExceptionWhenOverLimit() {
        when(limiter.allowOrCount(anyString(), anyInt(), anyInt())).thenReturn(false);
        assertThatThrownBy(() -> target.resendCode(new EmailArg("a@b.com")))
                .isInstanceOf(BizException.class)
                .satisfies(e -> assertThat(((BizException) e).getCode()).isEqualTo(429));
        assertThat(target.isCalled()).isFalse();
    }

    @Test
    void usesEmailAndIpAsBuckets() {
        target.resendCode(new EmailArg("a@b.com"));
        verify(limiter).allowOrCount("email:a@b.com", 1, 60);
        verify(limiter).allowOrCount(startsWith("ip:"), eq(5), eq(60));
    }

    static class Target {
        boolean called = false;

        @RateLimit({
                @RateLimit.Rule(key = RateLimit.LimitKey.EMAIL, limit = 1, windowSeconds = 60),
                @RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 5, windowSeconds = 60)
        })
        public void resendCode(EmailArg arg) {
            called = true;
        }

        public boolean isCalled() {
            return called;
        }
    }

    static class EmailArg {
        private final String email;

        EmailArg(String email) {
            this.email = email;
        }

        public String getEmail() {
            return email;
        }
    }
}
