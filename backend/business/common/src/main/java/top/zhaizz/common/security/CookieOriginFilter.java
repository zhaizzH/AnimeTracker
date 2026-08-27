package top.zhaizz.common.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import top.zhaizz.common.config.CorsProperties;

import java.io.IOException;

/** Cookie 认证端点只接受 CORS 白名单中的精确 Origin。 */
@Component
@RequiredArgsConstructor
public class CookieOriginFilter extends OncePerRequestFilter {
    private static final String REFRESH_PATH = "/api/client/auth/refresh";
    private static final String LOGOUT_PATH = "/api/client/auth/logout";
    private final CorsProperties corsProperties;

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
        if (origin == null || corsProperties.getAllowedOrigins() == null
                || !corsProperties.getAllowedOrigins().contains(origin)) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, "Origin 不被允许");
            return;
        }
        chain.doFilter(request, response);
    }
}