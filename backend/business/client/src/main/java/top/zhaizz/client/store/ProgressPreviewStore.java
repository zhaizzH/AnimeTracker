package top.zhaizz.client.store;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import top.zhaizz.client.model.ProgressPreviewSnapshot;
import top.zhaizz.client.model.ProgressPreviewStatus;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.client.constant.CollectionRedisKeys;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.infrastructure.redis.RedisUtil;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

/**
 * 收藏进度预览 Redis 快照与执行锁。
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class ProgressPreviewStore {

    /** 收藏进度预览快照的有效期。 */
    private static final Duration PREVIEW_TTL = Duration.ofMinutes(10);
    /** 收藏进度执行锁的有效期（秒）。 */
    private static final long EXECUTE_LOCK_TTL_SECONDS = 30L;

    /** Redis 访问工具。 */
    private final RedisUtil redisUtil;
    /** 用于序列化和反序列化 JSON。 */
    private final ObjectMapper objectMapper;

    /**
     * 保存预览快照，TTL 由调用方指定。
     * @param snapshot 包含用户、预览标识和进度状态的快照
     * @param ttl 有效期，写入 Redis 时截取为整分钟
     */
    public void save(ProgressPreviewSnapshot snapshot, Duration ttl) {
        redisUtil.set(previewKey(snapshot.getUserId(), snapshot.getPreviewId()),
                toJson(snapshot), ttl.toMinutes(), TimeUnit.MINUTES);
    }

    /**
     * 保存执行完成后的快照，TTL 重置为 10 分钟供幂等重放。
     * @param snapshot 包含用户、预览标识和进度状态的快照
     */
    public void saveCompleted(ProgressPreviewSnapshot snapshot) {
        redisUtil.set(previewKey(snapshot.getUserId(), snapshot.getPreviewId()),
                toJson(snapshot), PREVIEW_TTL.toMinutes(), TimeUnit.MINUTES);
    }

    /**
     * 按用户与预览标识读取快照，损坏数据不作为缓存未命中处理。
     * @param userId 快照所属用户 ID
     * @param previewId 预览标识
     * @return 快照；缓存缺失或 JSON 为 null 时返回空 Optional
     * @throws BizException JSON 无法解析时抛出 INTERNAL_ERROR
     */
    public Optional<ProgressPreviewSnapshot> find(Long userId, String previewId) {
        String json = redisUtil.get(previewKey(userId, previewId));
        if (json == null) return Optional.empty();
        try {
            return Optional.ofNullable(objectMapper.readValue(json, ProgressPreviewSnapshot.class));
        } catch (JsonProcessingException e) {
            log.error("收藏进度预览反序列化失败: userId={}, previewId={}", userId, previewId, e);
            throw new BizException(ErrorType.INTERNAL_ERROR, "预览状态读取失败");
        }
    }

    /**
     * 标记旧快照为 INVALIDATED 并保留至原 TTL 到期。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param previewId 已生成的进度预览标识
     */
    public void invalidate(Long userId, String previewId) {
        find(userId, previewId).ifPresent(s -> {
            s.setStatus(ProgressPreviewStatus.INVALIDATED);
            long ttlSeconds = s.getExpiresAt() == null ? PREVIEW_TTL.toSeconds()
                    : Math.max(0, Duration.between(OffsetDateTime.now(), s.getExpiresAt()).getSeconds());
            redisUtil.set(previewKey(userId, previewId), toJson(s), ttlSeconds, TimeUnit.SECONDS);
        });
    }

    /**
     * 以 30 秒有效期的 SET NX 锁获取预览执行权。
     * @param userId 快照所属用户 ID
     * @param previewId 预览标识
     * @return 成功获取执行权为 {@code true}；已有锁时为 {@code false}
     */
    public boolean tryLock(Long userId, String previewId) {
        return redisUtil.setIfAbsent(lockKey(userId, previewId), "1", EXECUTE_LOCK_TTL_SECONDS, TimeUnit.SECONDS);
    }

    /**
     * 释放执行锁。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param previewId 已生成的进度预览标识
     */
    public void unlock(Long userId, String previewId) {
        redisUtil.del(lockKey(userId, previewId));
    }

    /**
     * 构造用户进度预览快照的 Redis 键。
     *
     * @param userId 快照所属用户 ID
     * @param previewId 预览 ID
     * @return 稳定的 Redis 键
     */
    private String previewKey(Long userId, String previewId) {
        return CollectionRedisKeys.PROGRESS_PREVIEW + userId + ":" + previewId;
    }

    /**
     * 构造用户进度预览执行锁的 Redis 键。
     *
     * @param userId 锁所属用户 ID
     * @param previewId 预览 ID
     * @return 稳定的 Redis 键
     */
    private String lockKey(Long userId, String previewId) {
        return CollectionRedisKeys.PROGRESS_LOCK + userId + ":" + previewId;
    }

    /**
     * 序列化进度预览快照，失败时转换为统一业务异常。
     *
     * @param snapshot 待序列化的快照
     * @return JSON 文本
     * @throws BizException 快照无法序列化时抛出内部错误
     */
    private String toJson(ProgressPreviewSnapshot snapshot) {
        try {
            return objectMapper.writeValueAsString(snapshot);
        } catch (JsonProcessingException e) {
            throw new BizException(ErrorType.INTERNAL_ERROR, "预览状态序列化失败");
        }
    }
}
