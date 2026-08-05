package top.zhaizz.common.util;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

/**
 * 安全上下文工具，获取当前登录用户信息
 */
public class SecurityUtil {
    private SecurityUtil() {}

    /**
     * 获取当前登录用户 ID
     * JwtAuthenticationFilter 在认证时将 userId 设置到 Authentication.principal 中
     */
    public static Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return (Long) auth.getPrincipal();
    }

    /**
     * 获取当前登录用户 ID；未登录或 principal 非 Long 时返回 null（不抛异常）
     */
    public static Long getCurrentUserIdQuietly() {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            return auth != null && auth.getPrincipal() instanceof Long id ? id : null;
        } catch (Exception e) {
            return null;
        }
    }
}
