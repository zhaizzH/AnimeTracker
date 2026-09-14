package top.zhaizz.auth.security;

import lombok.RequiredArgsConstructor;
import top.zhaizz.pojo.dto.auth.ConsumedRefreshSession;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.stereotype.Component;
import top.zhaizz.auth.constant.AuthRedisKeys;
import top.zhaizz.infrastructure.redis.RedisUtil;

import java.time.Duration;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/** Redis 中 access/refresh 会话的索引与撤销操作。 */
@Component
@RequiredArgsConstructor
public class AuthSessionStore {
    /** 刷新索引兜底寿命，单位天，避免自然过期后残留摘要永久累积。 */
    private static final long REFRESH_INDEX_TTL_DAYS = Duration.ofDays(30).toDays();
    /** 会话摘要、凭据和用户索引的 Redis 访问入口。 */
    private final RedisUtil redis;

    /**
     * 保存刷新凭据摘要并登记用户索引。
     * @param rawToken 非空刷新明文，仅计算摘要
     * @param userId 凭据所属用户
     * @param startedAtEpochMs 首次登录时间，UTC 纪元毫秒
     * @param ttlMs 本次凭据有效期，单位毫秒
     */
    public void saveRefresh(String rawToken, Long userId, long startedAtEpochMs, long ttlMs) {
        String hash = hash(rawToken);
        redis.set(AuthRedisKeys.REFRESH + hash, userId + ":" + startedAtEpochMs, ttlMs, TimeUnit.MILLISECONDS);
        String indexKey = AuthRedisKeys.ACTIVE_REFRESH_TOKENS + userId;
        redis.sadd(indexKey, hash);
        // 凭据自然过期时仍限制索引寿命，避免遗留摘要永久累积。
        redis.expire(indexKey, REFRESH_INDEX_TTL_DAYS, TimeUnit.DAYS);
    }

    /**
     * 原子消费刷新凭据，保证同一凭据最多被一个并发请求取得。
     * @param rawToken 非空刷新明文
     * @return 用户及原始登录时间；凭据不存在或存储内容损坏时为空
     */
    public Optional<ConsumedRefreshSession> consumeRefresh(String rawToken) {
        String hash = hash(rawToken);
        String value = redis.getAndDelete(AuthRedisKeys.REFRESH + hash);
        if (value == null) return Optional.empty();
        String[] fields = value.split(":", 2);
        if (fields.length != 2) return Optional.empty();
        try {
            Long userId = Long.valueOf(fields[0]);
            long startedAt = Long.parseLong(fields[1]);
            redis.srem(AuthRedisKeys.ACTIVE_REFRESH_TOKENS + userId, hash);
            return Optional.of(new ConsumedRefreshSession(userId, startedAt));
        } catch (NumberFormatException e) {
            return Optional.empty();
        }
    }

    /**
     * 删除单个刷新凭据及其用户索引，已失效凭据不产生修改。
     * @param rawToken 非空刷新明文
     */
    public void revokeRefresh(String rawToken) {
        String hash = hash(rawToken);
        String value = redis.getAndDelete(AuthRedisKeys.REFRESH + hash);
        if (value == null) return;
        String[] fields = value.split(":", 2);
        if (fields.length == 2) redis.srem(AuthRedisKeys.ACTIVE_REFRESH_TOKENS + fields[0], hash);
    }

    /**
     * 删除访问白名单并移除对应用户索引。
     * @param rawToken 非空访问令牌明文
     */
    public void revokeAccess(String rawToken) {
        String hash = hash(rawToken);
        String userId = redis.get(AuthRedisKeys.TOKEN + hash);
        redis.del(AuthRedisKeys.TOKEN + hash);
        if (userId != null) redis.srem(AuthRedisKeys.ACTIVE_TOKENS + userId, hash);
    }

    /**
     * 撤销用户的全部访问和刷新凭据，并删除两个索引。
     * @param userId 业务层已决定撤销会话的用户 ID
     */
    public void revokeAll(Long userId) {
        String accessKey = AuthRedisKeys.ACTIVE_TOKENS + userId;
        Set<String> accessHashes = redis.smembers(accessKey);
        if (accessHashes != null) for (String hash : accessHashes) redis.del(AuthRedisKeys.TOKEN + hash);
        redis.del(accessKey);
        String refreshKey = AuthRedisKeys.ACTIVE_REFRESH_TOKENS + userId;
        Set<String> refreshHashes = redis.smembers(refreshKey);
        if (refreshHashes != null) for (String hash : refreshHashes) redis.del(AuthRedisKeys.REFRESH + hash);
        redis.del(refreshKey);
    }

    /**
     * 计算 Redis 使用的摘要，避免凭据明文入键。
     * @param rawToken 原始凭据
     * @return SHA-256 十六进制摘要
     */
    private String hash(String rawToken) { return DigestUtils.sha256Hex(rawToken); }
}
