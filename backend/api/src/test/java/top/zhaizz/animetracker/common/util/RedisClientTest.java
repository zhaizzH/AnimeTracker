package top.zhaizz.animetracker.common.util;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("test")
class RedisClientTest {

    @Autowired
    private RedisClient redisClient;

    @Test
    void setWithTtl_shouldStoreAndExpire() throws InterruptedException {
        String key = "test:ttl:" + System.currentTimeMillis();
        String value = "test-value";

        // 写入带 1 秒 TTL
        redisClient.set(key, value, 1, TimeUnit.SECONDS);
        assertEquals(value, redisClient.get(key));

        // 等待过期
        TimeUnit.MILLISECONDS.sleep(1100);
        assertNull(redisClient.get(key));
    }
}
