package top.zhaizz.client.constant;

/** 客户端认证、验证码和密码流程使用的 Redis 键前缀。 */
public final class ClientRedisKeys {
    /**
     * 禁止实例化仅提供静态操作的工具类。
     */
    private ClientRedisKeys() {
    }

    /** 注册邮箱验证码。 */
    public static final String EMAIL = "auth:email:";
    /** 修改邮箱验证码。 */
    public static final String EMAIL_CHANGE = "auth:email-change:";
    /** 密码重置验证码。 */
    public static final String PASSWORD_RESET = "auth:password-reset:";
    /** 登录失败计数。 */
    public static final String LOGIN_FAIL = "auth:login-fail:";
}
