package top.zhaizz.common.util;

import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Redis客户端
 */
@Component
public class RedisClient {
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 保存数据
     */
    public void set(String key, String value) {
        stringRedisTemplate.opsForValue().set(key, value);
    }

    /**
     * 保存数据（带过期时间）
     */
    public void set(String key, String value, long ttl, TimeUnit unit) {
        stringRedisTemplate.opsForValue().set(key, value, ttl, unit);
    }

    /**
     * 通过键获取对应的值
     */
    public String get(String key) {
        return stringRedisTemplate.opsForValue().get(key);
    }

    /**
     * 通过键删除对应的值
     */
    public void del(String key) {
        stringRedisTemplate.delete(key);
    }

    /**
     * 判断key是否存在
     */
    public Boolean exists(String key) {
        return stringRedisTemplate.hasKey(key);
    }

    /**
     * 获取集合中的所有成员
     */
    public Set<String> smembers(String key) {
        return stringRedisTemplate.opsForSet().members(key);
    }

    /**
     * 向集合添加一个或多个成员
     */
    public void sadd(String key, String... values) {
        stringRedisTemplate.opsForSet().add(key, values);
    }

    /**
     * 移除集合中一个或多个成员
     */
    public void srem(String key, String... values) {
        stringRedisTemplate.opsForSet().remove(key, (Object[]) values);
    }
}
