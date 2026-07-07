package top.zhaizz.common.util;

import jakarta.annotation.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

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
    public void set (String key,String value){
        stringRedisTemplate.opsForValue().set(key,value);
    }

    /**
     * 保存数据（带过期时间）
     * @param key   键
     * @param value 值
     * @param ttl   过期时间长度
     * @param unit  过期时间单位
     */
    public void set(String key, String value, long ttl, TimeUnit unit) {
        stringRedisTemplate.opsForValue().set(key, value, ttl, unit);
    }

    /**
     * 通过键获取对应的值
     * @param key 键
     * @return    值
     */
    public String get(String key){
        return stringRedisTemplate.opsForValue().get(key);
    }
    /**
     * 通过键删除对应的值
     * @param key 键
     */
    public void del(String key){
        stringRedisTemplate.delete(key);
    }
    /**
     * 判断key是否存在
     */
    public Boolean exists(String key){
        return stringRedisTemplate.hasKey(key);
    }
}
