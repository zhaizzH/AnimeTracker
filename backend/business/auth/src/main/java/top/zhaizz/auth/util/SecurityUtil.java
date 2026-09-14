package top.zhaizz.auth.util;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

/**
 * 读取安全上下文的用户身份，区分受保护业务和允许匿名的读取场景。
 */
public class SecurityUtil {
    /** 禁止实例化无状态身份读取工具。 */
    private SecurityUtil() {}

    /**
     * 获取当前登录用户 ID
     * JwtAuthenticationFilter 在认证时将 userId 设置到 Authentication.principal 中。
     * @return 已认证的用户 ID
     * @throws NullPointerException 当前上下文没有认证对象
     * @throws ClassCastException 当前 principal 不是 Long
     */
    public static Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return (Long) auth.getPrincipal();
    }

    /**
     * 安静读取用户 ID，供允许匿名身份的日志等场景使用。
     * @return 用户 ID；未登录、身份类型不匹配或读取异常时为 null
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
