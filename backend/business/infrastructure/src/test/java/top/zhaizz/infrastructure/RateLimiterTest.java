package top.zhaizz.infrastructure;

import org.junit.jupiter.api.Test;
import org.springframework.dao.DataAccessResourceFailureException;
import top.zhaizz.infrastructure.ratelimit.RateLimiter;
import top.zhaizz.infrastructure.redis.RedisUtil;
import java.util.concurrent.TimeUnit;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证限流迁移保留键格式、窗口、空值和故障契约 */
class RateLimiterTest {
    /** 边界次数放行、超限拒绝、空计数放行，重置删除同一个桶 */
    @Test
    void preservesQuotaWindowAndReset() {
        RedisUtil redis = mock(RedisUtil.class);
        RateLimiter limiter = new RateLimiter(redis);
        String key = "auth:rate-limit:email:test@example.test";
        when(redis.incr(key, 60, TimeUnit.SECONDS)).thenReturn(3L, 4L, null);
        assertTrue(limiter.allowOrCount("email:test@example.test", 3, 60));
        assertFalse(limiter.allowOrCount("email:test@example.test", 3, 60));
        assertTrue(limiter.allowOrCount("email:test@example.test", 3, 60));
        limiter.reset("email:test@example.test");
        verify(redis).del(key);
    }

    /** Redis 连接异常继续传播，不误认为空计数而放行 */
    @Test
    void propagatesRedisFailure() {
        RedisUtil redis = mock(RedisUtil.class);
        var failure = new DataAccessResourceFailureException("offline");
        when(redis.incr("auth:rate-limit:ip:127.0.0.1", 60, TimeUnit.SECONDS)).thenThrow(failure);
        assertSame(failure, assertThrows(DataAccessResourceFailureException.class,
                () -> new RateLimiter(redis).allowOrCount("ip:127.0.0.1", 3, 60)));
    }
}
