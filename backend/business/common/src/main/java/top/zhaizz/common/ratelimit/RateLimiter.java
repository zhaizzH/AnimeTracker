package top.zhaizz.common.ratelimit;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import top.zhaizz.common.constant.RedisKeys;
import top.zhaizz.common.util.RedisUtil;

import java.util.concurrent.TimeUnit;

/**
 * 基于 Redis INCR 的计数限流。Redis 不可用时放行（fail-open，个人项目可接受）。
 * ponytail: allowOrCount 对成功尝试也计数，调用方需在成功路径 reset
 */
@Component
@RequiredArgsConstructor
public class RateLimiter {

    private final RedisUtil redisUtil;

    /** 对桶自增计数并判断是否超限；Redis 不可用时放行返回 true */
    public boolean allowOrCount(String bucket, int limit, int windowSeconds) {
        Long count = redisUtil.incr(RedisKeys.RATE_LIMIT + bucket, windowSeconds, TimeUnit.SECONDS);
        return count == null || count <= limit;
    }

    /** 清除限流桶计数（业务成功后调用释放配额） */
    public void reset(String bucket) {
        redisUtil.del(RedisKeys.RATE_LIMIT + bucket);
    }
}
