package top.zhaizz.infrastructure.redis;

import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Redis 常用操作封装，统一走 StringRedisTemplate（String 值 + Set 成员）。
 */
@Component
public class RedisUtil {
    /** 字符串值与集合操作使用的 Redis 模板；连接异常直接传播给调用方。 */
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 保存字符串值，不设置过期时间。
     * @param key Redis 键
     * @param value 待保存字符串
     */
    public void set(String key, String value) {
        stringRedisTemplate.opsForValue().set(key, value);
    }

    /**
     * 保存字符串值并设置有效期。
     * @param key Redis 键
     * @param value 待保存字符串
     * @param ttl 有效时长
     * @param unit 时长单位
     */
    public void set(String key, String value, long ttl, TimeUnit unit) {
        stringRedisTemplate.opsForValue().set(key, value, ttl, unit);
    }

    /**
     * 仅在键不存在时写入并设置有效期。
     * @param key Redis 键
     * @param value 待保存字符串
     * @param ttl 有效时长
     * @param unit 时长单位
     * @return 写入成功为 true；键已存在或结果为空时为 false
     */
    public boolean setIfAbsent(String key, String value, long ttl, TimeUnit unit) {
        return Boolean.TRUE.equals(stringRedisTemplate.opsForValue().setIfAbsent(key, value, ttl, unit));
    }

    /**
     * 读取字符串值。
     * @param key Redis 键
     * @return 对应字符串；键不存在时为 null
     */
    public String get(String key) {
        return stringRedisTemplate.opsForValue().get(key);
    }

    /**
     * 修改已有键的有效期。
     * @param key Redis 键
     * @param timeout 有效时长
     * @param unit 时长单位
     */
    public void expire(String key, long timeout, TimeUnit unit) {
        stringRedisTemplate.expire(key, timeout, unit);
    }

    /**
     * 原子读取并删除字符串值。
     * @param key 待消费的 Redis 键
     * @return 删除前的字符串；键不存在时为 null
     */
    public String getAndDelete(String key) {
        return stringRedisTemplate.opsForValue().getAndDelete(key);
    }

    /**
     * 自增字符串计数器。
     * @param key 计数器键
     * @return 自增结果；流水线或事务中可能为 null
     */
    public Long incr(String key) {
        return stringRedisTemplate.opsForValue().increment(key);
    }

    /**
     * 自增计数器，仅首次创建时设置有效期；两条命令不具备原子性。
     * @param key 计数器键
     * @param ttl 首次写入时的有效时长
     * @param unit 时长单位
     * @return 自增结果；结果为空时不设置有效期
     */
    public Long incr(String key, long ttl, TimeUnit unit) {
        Long value = stringRedisTemplate.opsForValue().increment(key);
        if (value != null && value == 1) {
            stringRedisTemplate.expire(key, ttl, unit);
        }
        return value;
    }

    /**
     * 删除指定键。
     * @param key 待删除键；不存在时无副作用
     */
    public void del(String key) {
        stringRedisTemplate.delete(key);
    }

    /**
     * 检查键是否存在。
     * @param key Redis 键
     * @return 是否存在；流水线或事务中可能为 null
     */
    public Boolean exists(String key) {
        return stringRedisTemplate.hasKey(key);
    }

    /**
     * 读取集合的全部成员。
     * @param key 集合键
     * @return 成员集合；缺失键返回空集合，流水线或事务中可能为 null
     */
    public Set<String> smembers(String key) {
        return stringRedisTemplate.opsForSet().members(key);
    }

    /**
     * 向集合加入成员，已有成员不重复添加。
     * @param key 集合键
     * @param values 待加入成员
     */
    public void sadd(String key, String... values) {
        stringRedisTemplate.opsForSet().add(key, values);
    }

    /**
     * 从集合移除指定成员。
     * @param key 集合键
     * @param values 待移除成员；不存在的成员被忽略
     */
    public void srem(String key, String... values) {
        stringRedisTemplate.opsForSet().remove(key, (Object[]) values);
    }
}

