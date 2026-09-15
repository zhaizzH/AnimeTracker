package top.zhaizz.auth.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

/**
 * 签发和校验 JWT 访问令牌，Redis 白名单由请求认证过滤器独立检查
 */
@Component
public class JwtTokenProvider {

    /** 用于签发和验签的 HMAC 密钥，不得记录或输出 */
    private final SecretKey secretKey;
    /** 访问令牌有效期，单位毫秒 */
    private final long expirationMs;

    /**
     * 构建共享签名密钥与访问寿命
     * @param secret 满足 JWT 库 HMAC 长度要求的密钥文本
     * @param expirationMs 访问寿命，单位毫秒
     * @throws io.jsonwebtoken.security.WeakKeyException 密钥长度不足
     */
    public JwtTokenProvider(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.expiration}") long expirationMs) {
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.expirationMs = expirationMs;
    }

    /**
     * 生成携带用户 ID 和角色声明的签名访问令牌
     * @param userId 经过业务校验的用户 ID
     * @param role 经过业务校验的角色
     * @return 已签名访问令牌
     */
    public String generateToken(Long userId, String role) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + expirationMs);

        return Jwts.builder()
                .claim("userId", userId)
                .claim("role", role)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(secretKey)
                .compact();
    }

    /**
     * 验签并提取用户 ID 声明
     * @param token 签名访问令牌
     * @return 用户 ID；声明缺失时为 null
     * @throws JwtException 令牌签名、格式、有效期或声明类型无效
     * @throws IllegalArgumentException 令牌为空
     */
    public Long getUserIdFromToken(String token) {
        return parseClaims(token).get("userId", Long.class);
    }

    /**
     * 验签并提取角色声明
     * @param token 签名访问令牌
     * @return 角色；声明缺失时为 null
     * @throws JwtException 令牌签名、格式、有效期或声明类型无效
     * @throws IllegalArgumentException 令牌为空
     */
    public String getRoleFromToken(String token) {
        return parseClaims(token).get("role", String.class);
    }

    /**
     * 检查访问令牌签名与有效期，不查询 Redis 白名单
     * @param token 访问令牌，允许为空
     * @return 解析成功时为 true，格式、签名或有效期无效时为 false
     */
    public boolean validateToken(String token) {
        try {
            parseClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    /**
     * 验签并解析未过期的 JWT 声明
     * @param token 签名令牌
     * @return 已校验声明集合
     * @throws JwtException 签名、格式或有效期无效
     * @throws IllegalArgumentException 令牌为空
     */
    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
