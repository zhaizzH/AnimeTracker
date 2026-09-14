package top.zhaizz.auth.security;

import java.security.SecureRandom;
import java.time.Clock;
import java.util.HexFormat;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import top.zhaizz.auth.constant.AuthRedisKeys;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.infrastructure.redis.RedisUtil;
import top.zhaizz.pojo.dto.auth.AuthTokens;

/** 为已通过业务校验的身份签发凭据，并维护会话绝对寿命及 Redis 白名单。 */
@Service
@RequiredArgsConstructor
public class AuthTokenService {
    /** JWT 签名与访问凭据生成器。 */
    private final JwtTokenProvider jwtTokenProvider;
    /** 访问凭据白名单的 Redis 访问入口。 */
    private final RedisUtil redis;
    /** 刷新凭据与撤销索引存储。 */
    private final AuthSessionStore sessionStore;
    /** Access Token 有效期，单位毫秒。 */
    @Value("${jwt.expiration}")
    private long jwtExpiration;
    /** 单次刷新凭据有效期，单位毫秒。 */
    @Value("${jwt.refresh-expiration}")
    private long jwtRefreshExpiration;
    /** 从首次登录起计算的绝对会话上限，单位毫秒。 */
    @Value("${jwt.max-session-expiration}")
    private long jwtMaxSessionExpiration;
    /** 用于绝对会话寿命计算的 UTC 时钟。 */
    private Clock clock = Clock.systemUTC();
    /** 用于生成不可预测刷新凭据的安全随机源。 */
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    /**
     * 签发访问与刷新凭据；刷新保留原始登录起点并截断剩余寿命。
     * @param userId 已通过业务资格校验的用户 ID
     * @param role 已通过业务校验的角色
     * @param startedAtEpochMs 首次登录时间，UTC 纪元毫秒
     * @param refreshing 是否为已原子消费旧凭据后的续签
     * @return 新签发的凭据及 Cookie 秒数，不包含用户业务响应
     * @throws BizException 刷新已达到绝对寿命时返回 UNAUTHORIZED
     * @throws ArithmeticException 原始时间与最长寿命相加溢出
     */
    public AuthTokens issue(Long userId, String role, long startedAtEpochMs, boolean refreshing) {
        long refreshTtlMs = jwtRefreshExpiration;
        if (refreshing) {
            long remaining = Math.addExact(startedAtEpochMs, jwtMaxSessionExpiration) - clock.millis();
            if (remaining <= 0) throw new BizException(ErrorType.UNAUTHORIZED, "登录会话已达到最长有效期");
            refreshTtlMs = Math.min(refreshTtlMs, remaining);
        }
        String accessToken = jwtTokenProvider.generateToken(userId, role);
        String accessHash = DigestUtils.sha256Hex(accessToken);
        redis.set(AuthRedisKeys.TOKEN + accessHash, userId.toString(), jwtExpiration, TimeUnit.MILLISECONDS);
        redis.sadd(AuthRedisKeys.ACTIVE_TOKENS + userId, accessHash);
        String refreshToken = generateRefreshToken();
        sessionStore.saveRefresh(refreshToken, userId, startedAtEpochMs, refreshTtlMs);
        return new AuthTokens(accessToken, refreshToken, Math.max(1, refreshTtlMs / 1000));
    }

    /**
     * 生成 32 字节随机值的十六进制刷新凭据。
     * @return 64 个十六进制字符，不存储明文
     */
    private String generateRefreshToken() {
        byte[] bytes = new byte[32];
        SECURE_RANDOM.nextBytes(bytes);
        return HexFormat.of().formatHex(bytes);
    }
}

