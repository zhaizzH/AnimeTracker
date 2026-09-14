package top.zhaizz.auth.security;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.infrastructure.redis.RedisUtil;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证续签不延长绝对寿命，并保持刷新 Cookie 的秒数契约。 */
class AuthTokenServiceTest {
    /** 验证剩余寿命短于刷新窗口时，保存截断后的 TTL 和原始起点。 */
    @Test
    void capsRefreshAtAbsoluteLifetime() {
        JwtTokenProvider jwt = mock(JwtTokenProvider.class);
        RedisUtil redis = mock(RedisUtil.class);
        AuthSessionStore store = mock(AuthSessionStore.class);
        when(jwt.generateToken(42L, "USER")).thenReturn("access");
        AuthTokenService service = configuredService(jwt, redis, store, 9500L);
        var result = service.issue(42L, "USER", 1000L, true);
        assertEquals("access", result.accessToken());
        assertEquals(1L, result.refreshMaxAgeSeconds());
        assertTrue(result.refreshToken().matches("[0-9a-f]{64}"));
        verify(store).saveRefresh(result.refreshToken(), 42L, 1000L, 1500L);
    }

    /** 验证刷新窗口较短时按窗口发放，首次会话起点保持不变。 */
    @Test
    void capsRefreshAtConfiguredWindow() {
        JwtTokenProvider jwt = mock(JwtTokenProvider.class);
        AuthSessionStore store = mock(AuthSessionStore.class);
        when(jwt.generateToken(42L, "USER")).thenReturn("access");
        AuthTokenService service = configuredService(jwt, mock(RedisUtil.class), store, 2000L);
        var result = service.issue(42L, "USER", 1000L, true);
        assertEquals(4L, result.refreshMaxAgeSeconds());
        verify(store).saveRefresh(result.refreshToken(), 42L, 1000L, 4000L);
    }

    /** 验证达到绝对截止时不生成令牌、不写入新凭据。 */
    @Test
    void refusesExpiredSessionBeforeIssuing() {
        JwtTokenProvider jwt = mock(JwtTokenProvider.class);
        RedisUtil redis = mock(RedisUtil.class);
        AuthSessionStore store = mock(AuthSessionStore.class);
        AuthTokenService service = configuredService(jwt, redis, store, 11000L);
        assertThrows(BizException.class, () -> service.issue(42L, "USER", 1000L, true));
        verifyNoInteractions(jwt, redis, store);
    }

    /**
     * 构建固定时间与配置的认证能力，隔离真实时钟和外部 Redis。
     * @param jwt JWT 替身
     * @param redis Redis 替身
     * @param store 刷新存储替身
     * @param nowMs 固定 UTC 纪元毫秒
     * @return 配置了 4 秒刷新窗口和 10 秒绝对寿命的服务
     */
    private AuthTokenService configuredService(JwtTokenProvider jwt, RedisUtil redis, AuthSessionStore store, long nowMs) {
        AuthTokenService service = new AuthTokenService(jwt, redis, store);
        ReflectionTestUtils.setField(service, "clock", Clock.fixed(Instant.ofEpochMilli(nowMs), ZoneOffset.UTC));
        ReflectionTestUtils.setField(service, "jwtExpiration", 1000L);
        ReflectionTestUtils.setField(service, "jwtRefreshExpiration", 4000L);
        ReflectionTestUtils.setField(service, "jwtMaxSessionExpiration", 10000L);
        return service;
    }
}
