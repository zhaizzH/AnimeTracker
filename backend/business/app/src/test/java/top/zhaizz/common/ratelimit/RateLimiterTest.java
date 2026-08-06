package top.zhaizz.common.ratelimit;

import org.junit.jupiter.api.Test;
import top.zhaizz.common.util.RedisUtil;

import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RateLimiterTest {

    private final RedisUtil redisUtil = mock(RedisUtil.class);
    private final RateLimiter limiter = new RateLimiter(redisUtil);

    @Test
    void allowsWithinLimit() {
        when(redisUtil.incr(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(1L);
        assertThat(limiter.allowOrCount("bucket", 5, 60)).isTrue();
    }

    @Test
    void blocksOverLimit() {
        when(redisUtil.incr(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(6L);
        assertThat(limiter.allowOrCount("bucket", 5, 60)).isFalse();
    }

    @Test
    void failsOpenWhenRedisDown() {
        when(redisUtil.incr(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(null);
        assertThat(limiter.allowOrCount("bucket", 5, 60)).isTrue();
    }

    @Test
    void resetDeletesBucket() {
        limiter.reset("bucket");
        verify(redisUtil).del("auth:rate-limit:bucket");
    }
}
