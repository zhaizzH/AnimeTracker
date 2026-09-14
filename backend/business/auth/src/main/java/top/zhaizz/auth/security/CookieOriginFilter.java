package top.zhaizz.auth.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

/** Cookie 认证端点只接受 CORS 白名单中的精确 Origin。 */
public class CookieOriginFilter extends OncePerRequestFilter {
    /** 使用 Cookie 刷新凭据的接口路径。 */
    private static final String REFRESH_PATH = "/api/client/auth/refresh";
    /** 撤销 Cookie 会话的接口路径。 */
    private static final String LOGOUT_PATH = "/api/client/auth/logout";
    /** 允许的精确 Origin 列表；空列表拒绝所有目标请求。 */
    private final List<String> allowedOrigins;

    /**
     * 保存允许来源的不可变快照。
     * @param allowedOrigins 允许来源；null 按空列表处理
     */
    public CookieOriginFilter(List<String> allowedOrigins) {
        this.allowedOrigins = allowedOrigins == null ? List.of() : List.copyOf(allowedOrigins);
    }

    /**
     * 仅拦截刷新和退出的 POST 请求。
     * @param request 当前 HTTP 请求
     * @return 非 Cookie 认证写请求时为 true
     */
    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        if (!"POST".equalsIgnoreCase(request.getMethod())) return true;
        String path = request.getRequestURI();
        return !REFRESH_PATH.equals(path) && !LOGOUT_PATH.equals(path);
    }

    /**
     * 来源缺失或不匹配时返回 403，否则继续过滤链。
     * @param request 当前 HTTP 请求
     * @param response 当前 HTTP 响应
     * @param chain 后续过滤链
     * @throws ServletException 下游请求处理失败
     * @throws IOException 响应发送或下游 I/O 失败
     */
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String origin = request.getHeader("Origin");
        if (origin == null || !allowedOrigins.contains(origin)) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, "Origin 不被允许");
            return;
        }
        chain.doFilter(request, response);
    }
}
