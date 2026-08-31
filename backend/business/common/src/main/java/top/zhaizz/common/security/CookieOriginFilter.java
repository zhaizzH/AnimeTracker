package top.zhaizz.common.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

/** Cookie 认证端点只接受 CORS 白名单中的精确 Origin。 */
public class CookieOriginFilter extends OncePerRequestFilter {
    private static final String REFRESH_PATH = "/api/client/auth/refresh";
    private static final String LOGOUT_PATH = "/api/client/auth/logout";
    private final List<String> allowedOrigins;

    public CookieOriginFilter(List<String> allowedOrigins) {
        this.allowedOrigins = allowedOrigins == null ? List.of() : List.copyOf(allowedOrigins);
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        if (!"POST".equalsIgnoreCase(request.getMethod())) return true;
        String path = request.getRequestURI();
        return !REFRESH_PATH.equals(path) && !LOGOUT_PATH.equals(path);
    }

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
