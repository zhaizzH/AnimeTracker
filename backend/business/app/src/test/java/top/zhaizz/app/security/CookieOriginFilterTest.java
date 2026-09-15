package top.zhaizz.app.security;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import top.zhaizz.auth.security.CookieOriginFilter;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/** Cookie 认证端点 Origin 校验测试 */
class CookieOriginFilterTest {

    /** 记录是否继续执行的下游过滤链 */
    private FilterChain chain;
    /** 使用测试白名单构造的被测过滤器 */
    private CookieOriginFilter filter;
    /** 下游过滤链是否被调用 */
    private AtomicBoolean chainCalled;

    /** 重建白名单过滤器和调用标记，隔离每个场景 */
    @BeforeEach
    void setUp() {
        filter = new CookieOriginFilter(List.of("http://allowed.test"));
        chainCalled = new AtomicBoolean();
        chain = (request, response) -> chainCalled.set(true);
    }

    /** 验证白名单 Origin 才能调用 refresh 和 logout */
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

    /** 验证 Cookie 端点拒绝缺失或未知 Origin */
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

    /** 验证非 Cookie 认证路径跳过 Origin 校验 */
    @Test
    void skipsNonCookiePaths() throws Exception {
        MockHttpServletRequest request = request("/api/client/profile", null);
        MockHttpServletResponse response = new MockHttpServletResponse();
        filter.doFilter(request, response, chain);
        assertThat(chainCalled.get()).isTrue();
    }

    /**
     * 构造指定路径的 POST 请求，可省略 Origin 以测试拒绝行为
     * @param path 请求路径
     * @param origin 来源地址；为 null 时不添加请求头
     * @return 尚未执行过滤链的模拟请求
     */
    private MockHttpServletRequest request(String path, String origin) {
        MockHttpServletRequest request = new MockHttpServletRequest("POST", path);
        if (origin != null) request.addHeader("Origin", origin);
        return request;
    }
}
