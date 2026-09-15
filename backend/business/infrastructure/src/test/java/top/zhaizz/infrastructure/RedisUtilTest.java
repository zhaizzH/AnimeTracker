package top.zhaizz.infrastructure;

import org.junit.jupiter.api.Test;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.test.util.ReflectionTestUtils;
import top.zhaizz.infrastructure.redis.RedisUtil;
import java.util.concurrent.TimeUnit;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证计数窗口只在首次计数设置，后续尝试不延长窗口 */
class RedisUtilTest {
    /** 首次计数设置过期时间；后续计数和空结果不设置 */
    @Test
    @SuppressWarnings("unchecked")
    void expiresOnlyTheFirstIncrement() {
        StringRedisTemplate template = mock(StringRedisTemplate.class);
        ValueOperations<String, String> values = mock(ValueOperations.class);
        when(template.opsForValue()).thenReturn(values);
        when(values.increment("bucket")).thenReturn(1L, 2L, null);
        RedisUtil redis = new RedisUtil();
        ReflectionTestUtils.setField(redis, "stringRedisTemplate", template);
        assertEquals(1L, redis.incr("bucket", 20, TimeUnit.SECONDS));
        assertEquals(2L, redis.incr("bucket", 20, TimeUnit.SECONDS));
        assertNull(redis.incr("bucket", 20, TimeUnit.SECONDS));
        verify(template, times(1)).expire("bucket", 20, TimeUnit.SECONDS);
    }
}
