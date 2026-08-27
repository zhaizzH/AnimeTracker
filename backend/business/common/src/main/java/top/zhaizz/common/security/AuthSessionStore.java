package top.zhaizz.common.security;

import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.stereotype.Component;
import top.zhaizz.common.constant.RedisKeys;
import top.zhaizz.common.util.RedisUtil;

import java.time.Duration;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/** Redis 中 access/refresh 会话的索引与撤销操作。 */
@Component
@RequiredArgsConstructor
public class AuthSessionStore {
    private static final long REFRESH_INDEX_TTL_DAYS = Duration.ofDays(30).toDays();
    private final RedisUtil redis;

    public void saveRefresh(String rawToken, Long userId, long startedAtEpochMs, long ttlMs) {
        String hash = hash(rawToken);
        redis.set(RedisKeys.REFRESH + hash, userId + ":" + startedAtEpochMs, ttlMs, TimeUnit.MILLISECONDS);
        String indexKey = RedisKeys.ACTIVE_REFRESH_TOKENS + userId;
        redis.sadd(indexKey, hash);
        // Bound stale hashes when a refresh token expires without an explicit consume/revoke.
        redis.expire(indexKey, REFRESH_INDEX_TTL_DAYS, TimeUnit.DAYS);
    }

    /** GETDEL 保证轮换 token 在并发请求中只会被一个请求消费。 */
    public Optional<ConsumedRefreshSession> consumeRefresh(String rawToken) {
        String hash = hash(rawToken);
        String value = redis.getAndDelete(RedisKeys.REFRESH + hash);
        if (value == null) return Optional.empty();
        String[] fields = value.split(":", 2);
        if (fields.length != 2) return Optional.empty();
        try {
            Long userId = Long.valueOf(fields[0]);
            long startedAt = Long.parseLong(fields[1]);
            redis.srem(RedisKeys.ACTIVE_REFRESH_TOKENS + userId, hash);
            return Optional.of(new ConsumedRefreshSession(userId, startedAt));
        } catch (NumberFormatException e) {
            return Optional.empty();
        }
    }

    public void revokeRefresh(String rawToken) {
        String hash = hash(rawToken);
        String value = redis.getAndDelete(RedisKeys.REFRESH + hash);
        if (value == null) return;
        String[] fields = value.split(":", 2);
        if (fields.length == 2) redis.srem(RedisKeys.ACTIVE_REFRESH_TOKENS + fields[0], hash);
    }

    public void revokeAccess(String rawToken) {
        String hash = hash(rawToken);
        String userId = redis.get(RedisKeys.TOKEN + hash);
        redis.del(RedisKeys.TOKEN + hash);
        if (userId != null) redis.srem(RedisKeys.ACTIVE_TOKENS + userId, hash);
    }

    public void revokeAll(Long userId) {
        String accessKey = RedisKeys.ACTIVE_TOKENS + userId;
        Set<String> accessHashes = redis.smembers(accessKey);
        if (accessHashes != null) for (String hash : accessHashes) redis.del(RedisKeys.TOKEN + hash);
        redis.del(accessKey);
        String refreshKey = RedisKeys.ACTIVE_REFRESH_TOKENS + userId;
        Set<String> refreshHashes = redis.smembers(refreshKey);
        if (refreshHashes != null) for (String hash : refreshHashes) redis.del(RedisKeys.REFRESH + hash);
        redis.del(refreshKey);
    }

    private String hash(String rawToken) { return DigestUtils.sha256Hex(rawToken); }
}