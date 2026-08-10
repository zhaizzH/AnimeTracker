package top.zhaizz.common.util;

/** Redis Key 前缀常量集中管理 */
public final class RedisKeys {
    private RedisKeys() {}

    public static final String TOKEN = "auth:token:";
    public static final String REFRESH = "auth:refresh:";
    public static final String ACTIVE_TOKENS = "auth:active-tokens:";
    public static final String EMAIL = "auth:email:";
    public static final String EMAIL_CHANGE = "auth:email-change:";
    public static final String PASSWORD_RESET = "auth:password-reset:";
    public static final String LOGIN_FAIL = "auth:login-fail:";
    public static final String RATE_LIMIT = "auth:rate-limit:";
}
