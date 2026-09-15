package top.zhaizz.infrastructure.ratelimit;

/** 限流存储键定义；保留既有键前缀以兼容在线计数 */
public final class RateLimitKeys {
    /** 限流桶公共前缀，后接 email 或 ip 桶标识 */
    public static final String RATE_LIMIT = "auth:rate-limit:";

    /** 禁止实例化限流键定义 */
    private RateLimitKeys() {
    }
}
