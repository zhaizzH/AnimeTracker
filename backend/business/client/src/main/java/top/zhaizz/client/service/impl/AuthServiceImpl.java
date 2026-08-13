package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.UserConverter;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.client.service.AuthService;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.constant.RedisKeys;
import top.zhaizz.common.util.RedisUtil;
import top.zhaizz.common.security.JwtTokenProvider;
import top.zhaizz.pojo.dto.auth.LoginDTO;
import top.zhaizz.pojo.dto.auth.RegisterDTO;
import top.zhaizz.pojo.dto.auth.ResetPasswordDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.LoginVO;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * 认证服务实现
 */
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final RedisUtil redisUtil;
    private final JwtTokenProvider jwtTokenProvider;
    private final VerificationService verificationService;

    @Value("${jwt.expiration}")
    private long jwtExpiration; // 过期时间，单位毫秒

    @Value("${jwt.refresh-expiration}")
    private long jwtRefreshExpiration; // Refresh Token 过期时间，单位毫秒

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();
    @Value("${jwt.max-login-fails}")
    private int MAX_LOGIN_FAILS;
    @Value("${jwt.login-fail-window-minutes}")
    private long LOGIN_FAIL_WINDOW_MINUTES;

    @Override
    public void register(RegisterDTO request) {
        // 1. 检查用户名唯一性
        if (userMapper.existsByUsername(request.getUsername())) {
            throw new BizException(ErrorType.CONFLICT, "用户名已存在");
        }

        // 1.5 检查邮箱唯一性
        if (userMapper.existsByEmail(request.getEmail())) {
            throw new BizException(ErrorType.CONFLICT, "邮箱已被注册");
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
                        .eq(User::getEmail, email));

        return generateLoginVO(user);
    }

    @Override
    public LoginVO login(LoginDTO request) {
        // 0. 防爆破：失败计数达到阈值则锁定（5 分钟内第 6 次起直接拒绝，含正确密码）
        String failKey = RedisKeys.LOGIN_FAIL + request.getUsername();
        String failCount = redisUtil.get(failKey);
        if (failCount != null && Long.parseLong(failCount) >= MAX_LOGIN_FAILS) {
            throw new BizException(ErrorType.UNAUTHORIZED, "登录失败次数过多，请5分钟后再试");
        }

        // 1. 查找用户（支持用户名或邮箱登录）
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getUsername, request.getUsername())
                        .or()
                        .eq(User::getEmail, request.getUsername()));

        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            redisUtil.incr(failKey, LOGIN_FAIL_WINDOW_MINUTES, TimeUnit.MINUTES);
            throw new BizException(ErrorType.UNAUTHORIZED, "用户名或密码错误");
        }

        // 登录成功，清零失败计数
        redisUtil.del(failKey);

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
        redisUtil.del(RedisKeys.TOKEN + tokenHash);

        // 从用户活跃 token Set 中移除
        // 通过 jwtTokenProvider.getUserIdFromToken(token) 获取 userId
        try {
            Long userId = jwtTokenProvider.getUserIdFromToken(token);
            redisUtil.srem(RedisKeys.ACTIVE_TOKENS + userId, tokenHash);
        } catch (Exception e) {
            // token 已过期或无效，忽略
        }
    }

    /**
     * 刷新 Token
     * <p>
     * 校验 refresh token 有效性，轮换（删除旧 token），签发新的 access + refresh 对
     * </p>
     * <p>
     * ponytail: 并发 refresh 竞态——两线程同时用同一 refresh token refresh 都会成功。
     * 如需重用检测，升级为 Redis GETDEL 或 Lua 脚本原子操作。
     * </p>
     */
    @Override
    public LoginVO refresh(String refreshToken) {
        String refreshTokenHash = DigestUtils.sha256Hex(refreshToken);
        String userIdStr = redisUtil.get(RedisKeys.REFRESH + refreshTokenHash);
        if (userIdStr == null) {
            throw new BizException(ErrorType.UNAUTHORIZED, "refresh token 无效或已过期");
        }

        // 查询用户
        User user = userMapper.selectById(Long.valueOf(userIdStr));
        if (user == null) {
            // 用户已被删除，清理孤儿 refresh token
            redisUtil.del(RedisKeys.REFRESH + refreshTokenHash);
            throw new BizException(ErrorType.UNAUTHORIZED, "用户不存在");
        }

        // 先生成新 token 对，再删除旧的（防止生成过程中异常导致旧 token 已删、用户被锁定）
        LoginVO loginVO = generateLoginVO(user);
        redisUtil.del(RedisKeys.REFRESH + refreshTokenHash);
        return loginVO;
    }

    /**
     * 生成 JWT Token 与 Refresh Token，存入 Redis 白名单，返回 LoginVO
     */
    private LoginVO generateLoginVO(User user) {
        String accessToken = jwtTokenProvider.generateToken(user.getId(), user.getRole());
        String accessTokenHash = DigestUtils.sha256Hex(accessToken);
        redisUtil.set(RedisKeys.TOKEN + accessTokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);
        redisUtil.sadd(RedisKeys.ACTIVE_TOKENS + user.getId(), accessTokenHash);

        String refreshToken = generateRefreshToken();
        String refreshTokenHash = DigestUtils.sha256Hex(refreshToken);
        redisUtil.set(RedisKeys.REFRESH + refreshTokenHash, user.getId().toString(), jwtRefreshExpiration,
                TimeUnit.MILLISECONDS);

        return new LoginVO(accessToken, refreshToken, UserConverter.toUserVO(user));
    }

    private String generateRefreshToken() {
        byte[] bytes = new byte[32];
        SECURE_RANDOM.nextBytes(bytes);
        StringBuilder sb = new StringBuilder(64);
        for (byte b : bytes) {
            sb.append(String.format("%02x", b & 0xFF));
        }
        return sb.toString();
    }

    @Override
    public void forgotPassword(String email) {
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getEmail, email));
        if (user == null) {
            // 静默返回，防止邮箱枚举
            return;
        }
        verificationService.sendPasswordResetCode(email);
    }

    @Override
    public void resetPassword(ResetPasswordDTO request) {
        // 1. 校验验证码
        verificationService.verifyPasswordResetCode(request.getEmail(), request.getCode());

        // 2. 查用户
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getEmail, request.getEmail()));
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }

        // 3. 更新密码
        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);

        // 4. 踢出所有设备
        String userTokensKey = RedisKeys.ACTIVE_TOKENS + user.getId();
        Set<String> tokenHashes = redisUtil.smembers(userTokensKey);
        if (tokenHashes != null) {
            for (String hash : tokenHashes) {
                redisUtil.del(RedisKeys.TOKEN + hash);
            }
        }
        redisUtil.del(userTokensKey);

        // 5. 删除验证码
        redisUtil.del(RedisKeys.PASSWORD_RESET + request.getEmail());
    }
}
