package top.zhaizz.auth.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.lang.NonNull;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;
import top.zhaizz.auth.constant.AuthRedisKeys;
import top.zhaizz.infrastructure.redis.RedisUtil;

import java.io.IOException;

/**
 * 提取 Authorization 凭据，通过 JWT 和白名单双重检查后建立请求身份。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    /** 访问令牌签名、过期与身份声明校验入口。 */
    private final JwtTokenProvider jwtTokenProvider;
    /** 访问凭据白名单查询入口。 */
    private final RedisUtil redisUtil;
    /** Bearer 令牌所在的 HTTP 请求头。 */
    private static final String AUTHORIZATION_HEADER = "Authorization";
    /** 必须精确匹配的 Bearer 认证前缀。 */
    public static final String BEARER_PREFIX = "Bearer ";

    /**
     * JWT 与 Redis 白名单均通过时建立身份，否则保持未认证并继续过滤链。
     * @param request 当前 HTTP 请求
     * @param response 当前 HTTP 响应
     * @param chain 后续过滤链
     * @throws ServletException 后续过滤处理失败
     * @throws IOException 后续请求或响应 I/O 失败
     */
    @Override
    protected void doFilterInternal(@NonNull HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain chain) throws ServletException, IOException {

        String token = resolveToken(request);

        if (StringUtils.hasText(token)) {
            if (jwtTokenProvider.validateToken(token)) {
                // 先算 SHA256 摘要,防止明文 token 进 Redis 键
                String tokenHash = DigestUtils.sha256Hex(token);
                Boolean exists = redisUtil.exists(AuthRedisKeys.TOKEN + tokenHash);

                if (Boolean.TRUE.equals(exists)) {
                    Long userId = jwtTokenProvider.getUserIdFromToken(token);
                    String role = jwtTokenProvider.getRoleFromToken(token);

                    UserPrincipal principal = new UserPrincipal(userId, role);
                    principal.setAuthenticated(true);
                    SecurityContextHolder.getContext().setAuthentication(principal);
                } else {
                    log.debug("token 不在 Redis 白名单，视为未认证");
                }
            } else {
                log.debug("token 校验失败，视为未认证");
            }
        }

        chain.doFilter(request, response);
    }

    /**
     * 从请求头提取 Bearer 凭据。
     * @param request 当前请求
     * @return 去掉前缀的令牌；请求头缺失或前缀不匹配时为 null
     */
    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith(BEARER_PREFIX)) {
            return bearerToken.substring(BEARER_PREFIX.length());
        }
        return null;
    }
}
