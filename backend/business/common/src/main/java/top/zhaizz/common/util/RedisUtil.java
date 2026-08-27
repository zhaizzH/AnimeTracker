package top.zhaizz.common.util;

import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Redis 常用操作封装，统一走 StringRedisTemplate（String 值 + Set 成员）
 */
@Component
public class RedisUtil {
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
     * 键不存在时设置并返回 true，已存在则返回 false（SET NX，用于分布式锁）
     */
    public boolean setIfAbsent(String key, String value, long ttl, TimeUnit unit) {
        return Boolean.TRUE.equals(stringRedisTemplate.opsForValue().setIfAbsent(key, value, ttl, unit));
    }

    /**
     * 通过键获取对应的值
     */
    public String get(String key) {
        return stringRedisTemplate.opsForValue().get(key);
    }

    /**
     * 获取并删除字符串值（Redis GETDEL，保证 refresh token 只能被消费一次）
     */
    public String getAndDelete(String key) {
        return stringRedisTemplate.opsForValue().getAndDelete(key);
    }

    /**
     * 自增并返回新值
     */
    public Long incr(String key) {
        return stringRedisTemplate.opsForValue().increment(key);
    }

    /**
     * 自增并设置过期时间（仅在首次创建时设置 TTL）
     * ponytail: incr 与 expire 非原子，极端并发下窗口期可能拉长，无害
     */
    public Long incr(String key, long ttl, TimeUnit unit) {
        Long value = stringRedisTemplate.opsForValue().increment(key);
        if (value != null && value == 1) {
            stringRedisTemplate.expire(key, ttl, unit);
        }
        return value;
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
