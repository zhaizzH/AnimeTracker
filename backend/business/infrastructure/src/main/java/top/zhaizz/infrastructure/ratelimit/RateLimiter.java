package top.zhaizz.infrastructure.ratelimit;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import top.zhaizz.infrastructure.redis.RedisUtil;

import java.util.concurrent.TimeUnit;

/**
 * 基于 Redis INCR 计数限流；空计数结果放行，Redis 异常向调用方传播。
 * <p>成功尝试也计数，是否重置由业务调用方决定。
 */
@Component
@RequiredArgsConstructor
public class RateLimiter {

    /** 执行计数及删除操作的 Redis 能力。 */
    private final RedisUtil redisUtil;

    /**
     * 计数当前尝试并检查固定窗口配额。
     * @param bucket 限流桶后缀
     * @param limit 允许的最大尝试次数
     * @param windowSeconds 首次计数设置的窗口，单位秒
     * @return 计数为空或未超过限额时为 true；否则为 false
     */
    public boolean allowOrCount(String bucket, int limit, int windowSeconds) {
        Long count = redisUtil.incr(RateLimitKeys.RATE_LIMIT + bucket, windowSeconds, TimeUnit.SECONDS);
        return count == null || count <= limit;
    }

    /**
     * 清除限流桶计数，由业务成功路径按需调用。
     * @param bucket 要重置的桶后缀
     */
    public void reset(String bucket) {
        redisUtil.del(RateLimitKeys.RATE_LIMIT + bucket);
    }
}
