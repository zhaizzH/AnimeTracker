package top.zhaizz.auth.constant;

/** 认证凭据与用户会话索引的 Redis 前缀，保持既有存量键兼容。 */
public final class AuthRedisKeys {
    /** 禁止实例化常量容器。 */
    private AuthRedisKeys() {}
    /** Access Token 摘要到用户 ID 的白名单。 */
    public static final String TOKEN = "auth:token:";
    /** Refresh Token 摘要到用户与原始登录时间的映射。 */
    public static final String REFRESH = "auth:refresh:";
    /** 用户拥有的 Access Token 摘要集合。 */
    public static final String ACTIVE_TOKENS = "auth:active-tokens:";
    /** 用户拥有的 Refresh Token 摘要集合。 */
    public static final String ACTIVE_REFRESH_TOKENS = "auth:active-refresh:";
}
