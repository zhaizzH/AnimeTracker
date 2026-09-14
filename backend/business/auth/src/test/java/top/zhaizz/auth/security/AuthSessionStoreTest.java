package top.zhaizz.auth.security;

import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.apache.commons.codec.digest.DigestUtils;
import org.junit.jupiter.api.Test;
import top.zhaizz.infrastructure.redis.RedisUtil;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证刷新单次消费与凭据、用户索引一致撤销。 */
class AuthSessionStoreTest {
    /** 验证 GETDEL 第二次返回空，不允许已消费凭据重放。 */
    @Test
    void consumesRefreshOnlyOnceAndPreservesStart() {
        RedisUtil redis = mock(RedisUtil.class);
        String hash = DigestUtils.sha256Hex("refresh");
        when(redis.getAndDelete("auth:refresh:" + hash)).thenReturn("42:1000", (String) null);
        AuthSessionStore store = new AuthSessionStore(redis);
        var consumed = store.consumeRefresh("refresh").orElseThrow();
        assertEquals(42L, consumed.userId());
        assertEquals(1000L, consumed.startedAtEpochMs());
        assertTrue(store.consumeRefresh("refresh").isEmpty());
        verify(redis).srem("auth:active-refresh:42", hash);
    }

    /** 验证损坏的元数据被消费后拒绝续签。 */
    @Test
    void rejectsMalformedRefreshMetadata() {
        RedisUtil redis = mock(RedisUtil.class);
        when(redis.getAndDelete(anyString())).thenReturn("broken", "42:invalid");
        AuthSessionStore store = new AuthSessionStore(redis);
        assertTrue(store.consumeRefresh("one").isEmpty());
        assertTrue(store.consumeRefresh("two").isEmpty());
        verify(redis, never()).srem(anyString(), anyString());
    }

    /** 验证撤销用户会话会删除两类凭据和两个用户索引。 */
    @Test
    void revokesAllCredentialsAndIndexes() {
        RedisUtil redis = mock(RedisUtil.class);
        when(redis.smembers("auth:active-tokens:42")).thenReturn(Set.of("access-hash"));
        when(redis.smembers("auth:active-refresh:42")).thenReturn(Set.of("refresh-hash"));
        new AuthSessionStore(redis).revokeAll(42L);
        verify(redis).del("auth:token:access-hash");
        verify(redis).del("auth:refresh:refresh-hash");
        verify(redis).del("auth:active-tokens:42");
        verify(redis).del("auth:active-refresh:42");
    }

    /** 验证单会话撤销保留其他凭据并移除被撤销摘要。 */
    @Test
    void revokesSingleAccessAndRefresh() {
        RedisUtil redis = mock(RedisUtil.class);
        String hash = DigestUtils.sha256Hex("token");
        when(redis.get("auth:token:" + hash)).thenReturn("42");
        when(redis.getAndDelete("auth:refresh:" + hash)).thenReturn("42:1000");
        AuthSessionStore store = new AuthSessionStore(redis);
        store.revokeAccess("token");
        store.revokeRefresh("token");
        verify(redis).del("auth:token:" + hash);
        verify(redis).srem("auth:active-tokens:42", hash);
        verify(redis).srem("auth:active-refresh:42", hash);
    }

    /** 验证只保存摘要、既有值格式和毫秒寿命，索引保留 30 天兜底。 */
    @Test
    void savesOnlyHashedRefreshWithOriginalStart() {
        RedisUtil redis = mock(RedisUtil.class);
        String hash = DigestUtils.sha256Hex("secret");
        new AuthSessionStore(redis).saveRefresh("secret", 42L, 1000L, 2500L);
        verify(redis).set("auth:refresh:" + hash, "42:1000", 2500L, TimeUnit.MILLISECONDS);
        verify(redis).sadd("auth:active-refresh:42", hash);
        verify(redis).expire("auth:active-refresh:42", 30L, TimeUnit.DAYS);
    }
}
