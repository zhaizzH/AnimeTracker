package top.zhaizz.client.store;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import top.zhaizz.client.model.ProgressPreviewSnapshot;
import top.zhaizz.client.model.ProgressPreviewStatus;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.constant.RedisKeys;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.util.RedisUtil;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

/**
 * 收藏进度预览 Redis 快照与执行锁
 */
@Component
@RequiredArgsConstructor
public class ProgressPreviewStore {

    private static final Duration PREVIEW_TTL = Duration.ofMinutes(10);
    private static final long EXECUTE_LOCK_TTL_SECONDS = 30L;

    private final RedisUtil redisUtil;
    private final ObjectMapper objectMapper;

    /** 保存预览快照，TTL 由调用方指定 */
    public void save(ProgressPreviewSnapshot snapshot, Duration ttl) {
        redisUtil.set(previewKey(snapshot.getUserId(), snapshot.getPreviewId()),
                toJson(snapshot), ttl.toMinutes(), TimeUnit.MINUTES);
    }

    /** 保存执行完成后的快照，TTL 重置为 10 分钟供幂等重放 */
    public void saveCompleted(ProgressPreviewSnapshot snapshot) {
        redisUtil.set(previewKey(snapshot.getUserId(), snapshot.getPreviewId()),
                toJson(snapshot), PREVIEW_TTL.toMinutes(), TimeUnit.MINUTES);
    }

    /** 按用户与预览 ID 查找快照，缺失或反序列化失败返回 empty */
    public Optional<ProgressPreviewSnapshot> find(Long userId, String previewId) {
        String json = redisUtil.get(previewKey(userId, previewId));
        if (json == null) return Optional.empty();
        try {
            return Optional.ofNullable(objectMapper.readValue(json, ProgressPreviewSnapshot.class));
        } catch (JsonProcessingException e) {
            return Optional.empty();
        }
    }

    /** 标记旧快照为 INVALIDATED 并保留至原 TTL 到期 */
    public void invalidate(Long userId, String previewId) {
        find(userId, previewId).ifPresent(s -> {
            s.setStatus(ProgressPreviewStatus.INVALIDATED);
            long ttlSeconds = s.getExpiresAt() == null ? PREVIEW_TTL.toSeconds()
                    : Math.max(0, Duration.between(OffsetDateTime.now(), s.getExpiresAt()).getSeconds());
            redisUtil.set(previewKey(userId, previewId), toJson(s), ttlSeconds, TimeUnit.SECONDS);
        });
    }

    /** 以 30 秒 SET NX 锁获取执行权 */
    public boolean tryLock(Long userId, String previewId) {
        return redisUtil.setIfAbsent(lockKey(userId, previewId), "1", EXECUTE_LOCK_TTL_SECONDS, TimeUnit.SECONDS);
    }

    /** 释放执行锁 */
    public void unlock(Long userId, String previewId) {
        redisUtil.del(lockKey(userId, previewId));
    }

    private String previewKey(Long userId, String previewId) {
        return RedisKeys.COLLECTION_PROGRESS_PREVIEW + userId + ":" + previewId;
    }

    private String lockKey(Long userId, String previewId) {
        return RedisKeys.COLLECTION_PROGRESS_LOCK + userId + ":" + previewId;
    }

    private String toJson(ProgressPreviewSnapshot snapshot) {
        try {
            return objectMapper.writeValueAsString(snapshot);
        } catch (JsonProcessingException e) {
            throw new BizException(ErrorType.INTERNAL_ERROR, "预览状态序列化失败");
        }
    }
}
