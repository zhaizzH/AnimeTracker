package top.zhaizz.app.security;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import top.zhaizz.common.security.CookieOriginFilter;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class CookieOriginFilterTest {

    private FilterChain chain;
    private CookieOriginFilter filter;
    private AtomicBoolean chainCalled;

    @BeforeEach
    void setUp() {
        filter = new CookieOriginFilter(List.of("http://allowed.test"));
        chainCalled = new AtomicBoolean();
        chain = (request, response) -> chainCalled.set(true);
    }

    @Test
    void allowsRefreshAndLogoutOnlyForWhitelistedOrigin() throws Exception {
        MockHttpServletRequest refresh = request("/api/client/auth/refresh", "http://allowed.test");
        MockHttpServletResponse refreshResponse = new MockHttpServletResponse();
        filter.doFilter(refresh, refreshResponse, chain);
        assertThat(chainCalled.get()).isTrue();

        chainCalled.set(false);
        MockHttpServletRequest logout = request("/api/client/auth/logout", "http://allowed.test");
        MockHttpServletResponse logoutResponse = new MockHttpServletResponse();
        filter.doFilter(logout, logoutResponse, chain);
        assertThat(chainCalled.get()).isTrue();
    }

    @Test
    void rejectsMissingOrUnknownOriginOnCookieEndpoints() throws Exception {
        MockHttpServletRequest missing = request("/api/client/auth/refresh", null);
        MockHttpServletResponse missingResponse = new MockHttpServletResponse();
        filter.doFilter(missing, missingResponse, chain);
        assertThat(missingResponse.getStatus()).isEqualTo(403);

        MockHttpServletRequest unknown = request("/api/client/auth/logout", "http://evil.test");
        MockHttpServletResponse unknownResponse = new MockHttpServletResponse();
        filter.doFilter(unknown, unknownResponse, chain);
        assertThat(unknownResponse.getStatus()).isEqualTo(403);
        assertThat(chainCalled.get()).isFalse();
    }

    @Test
    void skipsNonCookiePaths() throws Exception {
        MockHttpServletRequest request = request("/api/client/profile", null);
        MockHttpServletResponse response = new MockHttpServletResponse();
        filter.doFilter(request, response, chain);
        assertThat(chainCalled.get()).isTrue();
    }

    private MockHttpServletRequest request(String path, String origin) {
        MockHttpServletRequest request = new MockHttpServletRequest("POST", path);
        if (origin != null) request.addHeader("Origin", origin);
        return request;
    }
}
