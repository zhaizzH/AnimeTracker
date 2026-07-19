package top.zhaizz.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.util.RedisClient;
import top.zhaizz.common.security.JwtTokenProvider;
import top.zhaizz.user.converter.UserConverter;
import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.user.mapper.UserMapper;
import top.zhaizz.user.service.AuthService;
import top.zhaizz.user.service.VerificationService;
import top.zhaizz.pojo.vo.LoginVO;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * 认证服务实现
 */
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final RedisClient redisClient;
    private final JwtTokenProvider jwtTokenProvider;
    private final VerificationService verificationService;

    @Value("${jwt.expiration}")
    private long jwtExpiration; // 过期时间，单位毫秒

    @Value("${jwt.refresh-expiration}")
    private long jwtRefreshExpiration; // Refresh Token 过期时间，单位毫秒

    private static final String REDIS_TOKEN_PREFIX = "auth:token:";
    private static final String REDIS_REFRESH_PREFIX = "auth:refresh:";

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    @Override
    public void register(RegisterDTO request) {
        // 1. 检查用户名唯一性
        if (userMapper.existsByUsername(request.getUsername())) {
            throw new BizException(ErrorType.CONFLICT, "用户名已存在");
        }

        // 2. 创建用户实体
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setNickname(request.getUsername()); // 默认昵称为用户名
        user.setRole("USER");
        user.setEmailVerified(false);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());

        // 3. 保存
        userMapper.insert(user);

        // 4. 发送验证码邮件
        verificationService.sendVerificationCode(request.getEmail());
    }

    @Override
    public void resendCode(String email) {
        verificationService.sendVerificationCode(email);
    }

    @Override
    public LoginVO verifyEmail(String email, String code) {
        // 1. 校验验证码（内部会更新 email_verified = true）
        verificationService.verifyEmail(email, code);

        // 2. 查找用户
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getEmail, email)
        );

        return generateLoginVO(user);
    }

    @Override
    public LoginVO login(LoginDTO request) {
        // 1. 查找用户（支持用户名或邮箱登录）
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getUsername, request.getUsername())
                        .or()
                        .eq(User::getEmail, request.getUsername())
        );

        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ErrorType.UNAUTHORIZED, "用户名或密码错误");
        }

        // 2. 检查邮箱是否已验证
        if (Boolean.FALSE.equals(user.getEmailVerified())) {
            throw new BizException(ErrorType.EMAIL_NOT_VERIFIED,
                    "邮箱未验证，请先验证邮箱",
                    Map.of("email", user.getEmail()));
        }

        return generateLoginVO(user);
    }

    @Override
    public void logout(String token) {
        // 计算 SHA256 摘要，从 Redis 删除
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.del(REDIS_TOKEN_PREFIX + tokenHash);

        // 同时清理 refresh token
        // 注意：当前 logout 方法只有 token 参数，没有 refreshToken
        // 这里清理 access token，refresh token 由前端自行清除或自然过期
    }

    /**
     * 刷新 Token
     * <p>校验 refresh token 有效性，轮换（删除旧 token），签发新的 access + refresh 对</p>
     * <p>ponytail: 并发 refresh 竞态——两线程同时用同一 refresh token refresh 都会成功。
     * 如需重用检测，升级为 Redis GETDEL 或 Lua 脚本原子操作。</p>
     */
    @Override
    public LoginVO refresh(String refreshToken) {
        String refreshTokenHash = DigestUtils.sha256Hex(refreshToken);
        String userIdStr = redisClient.get(REDIS_REFRESH_PREFIX + refreshTokenHash);
        if (userIdStr == null) {
            throw new BizException(ErrorType.UNAUTHORIZED, "refresh token 无效或已过期");
        }

        // 查询用户
        User user = userMapper.selectById(Long.valueOf(userIdStr));
        if (user == null) {
            // 用户已被删除，清理孤儿 refresh token
            redisClient.del(REDIS_REFRESH_PREFIX + refreshTokenHash);
            throw new BizException(ErrorType.UNAUTHORIZED, "用户不存在");
        }

        // 先生成新 token 对，再删除旧的（防止生成过程中异常导致旧 token 已删、用户被锁定）
        LoginVO loginVO = generateLoginVO(user);
        redisClient.del(REDIS_REFRESH_PREFIX + refreshTokenHash);
        return loginVO;
    }

    /**
     * 生成 JWT Token 与 Refresh Token，存入 Redis 白名单，返回 LoginVO
     */
    private LoginVO generateLoginVO(User user) {
        String accessToken = jwtTokenProvider.generateToken(user.getId(), user.getRole());
        String accessTokenHash = DigestUtils.sha256Hex(accessToken);
        redisClient.set(REDIS_TOKEN_PREFIX + accessTokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);

        String refreshToken = generateRefreshToken();
        String refreshTokenHash = DigestUtils.sha256Hex(refreshToken);
        redisClient.set(REDIS_REFRESH_PREFIX + refreshTokenHash, user.getId().toString(), jwtRefreshExpiration, TimeUnit.MILLISECONDS);

        return new LoginVO(accessToken, refreshToken, UserConverter.toUserVO(user));
    }

    /**
     * 生成 64 位十六进制随机 Refresh Token
     */
    private String generateRefreshToken() {
        byte[] bytes = new byte[32];
        SECURE_RANDOM.nextBytes(bytes);
        StringBuilder sb = new StringBuilder(64);
        for (byte b : bytes) {
            sb.append(String.format("%02x", b & 0xFF));
        }
        return sb.toString();
    }
}
