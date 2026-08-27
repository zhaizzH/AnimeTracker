package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.UserConverter;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.client.model.IssuedAuthSession;
import top.zhaizz.client.service.AuthService;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.constant.RedisKeys;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.security.AuthSessionStore;
import top.zhaizz.common.security.ConsumedRefreshSession;
import top.zhaizz.common.security.JwtTokenProvider;
import top.zhaizz.common.util.RedisUtil;
import top.zhaizz.pojo.dto.auth.LoginDTO;
import top.zhaizz.pojo.dto.auth.RegisterDTO;
import top.zhaizz.pojo.dto.auth.ResetPasswordDTO;
import top.zhaizz.pojo.entity.User;

import java.security.SecureRandom;
import java.time.Clock;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {
    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final RedisUtil redisUtil;
    private final JwtTokenProvider jwtTokenProvider;
    private final VerificationService verificationService;
    private final AuthSessionStore sessionStore;

    @Value("${jwt.expiration}")
    private long jwtExpiration;
    @Value("${jwt.refresh-expiration}")
    private long jwtRefreshExpiration;
    @Value("${jwt.max-session-expiration}")
    private long jwtMaxSessionExpiration;
    @Value("${jwt.max-login-fails}")
    private int maxLoginFails;
    @Value("${jwt.login-fail-window-minutes}")
    private long loginFailWindowMinutes;

    private Clock clock = Clock.systemUTC();
    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    @Override
    public void register(RegisterDTO request) {
        if (userMapper.existsByUsername(request.getUsername())) throw new BizException(ErrorType.CONFLICT, "用户名已存在");
        if (userMapper.existsByEmail(request.getEmail())) throw new BizException(ErrorType.CONFLICT, "邮箱已被注册");
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setNickname(request.getUsername());
        user.setRole("USER");
        user.setEmailVerified(false);
        user.setEnabled(true);
        user.setCreatedAt(LocalDateTime.now(clock));
        user.setUpdatedAt(LocalDateTime.now(clock));
        userMapper.insert(user);
        verificationService.sendVerificationCode(request.getEmail());
    }

    @Override
    public void resendCode(String email) { verificationService.sendVerificationCode(email); }

    @Override
    public IssuedAuthSession verifyEmail(String email, String code) {
        verificationService.verifyEmail(email, code);
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getEmail, email));
        return generateLoginSession(user, clock.millis());
    }

    @Override
    public IssuedAuthSession login(LoginDTO request) {
        String failKey = RedisKeys.LOGIN_FAIL + request.getUsername();
        String failCount = redisUtil.get(failKey);
        if (failCount != null && Long.parseLong(failCount) >= maxLoginFails) {
            throw new BizException(ErrorType.UNAUTHORIZED, "登录失败次数过多，请5分钟后再试");
        }
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>()
                .eq(User::getUsername, request.getUsername()).or().eq(User::getEmail, request.getUsername()));
        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            redisUtil.incr(failKey, loginFailWindowMinutes, TimeUnit.MINUTES);
            throw new BizException(ErrorType.UNAUTHORIZED, "用户名或密码错误");
        }
        redisUtil.del(failKey);
        if (Boolean.FALSE.equals(user.getEmailVerified())) {
            throw new BizException(ErrorType.EMAIL_NOT_VERIFIED, "邮箱未验证，请先验证邮箱", Map.of("email", user.getEmail()));
        }
        return generateLoginSession(user, clock.millis());
    }

    @Override
    public void logout(String accessToken, String refreshToken) {
        if (accessToken != null && !accessToken.isBlank()) sessionStore.revokeAccess(accessToken);
        if (refreshToken != null && !refreshToken.isBlank()) sessionStore.revokeRefresh(refreshToken);
    }

    @Override
    public IssuedAuthSession refresh(String refreshToken) {
        if (refreshToken == null || refreshToken.isBlank()) {
            throw new BizException(ErrorType.UNAUTHORIZED, "refresh token 无效或已过期");
        }
        Optional<ConsumedRefreshSession> consumed = sessionStore.consumeRefresh(refreshToken);
        if (consumed.isEmpty()) throw new BizException(ErrorType.UNAUTHORIZED, "refresh token 无效或已过期");
        ConsumedRefreshSession session = consumed.get();
        User user = userMapper.selectById(session.userId());
        if (user == null || Boolean.FALSE.equals(user.getEnabled())) {
            throw new BizException(ErrorType.UNAUTHORIZED, "账号不可用");
        }
        long remainingAbsolute = Math.addExact(session.startedAtEpochMs(), jwtMaxSessionExpiration) - clock.millis();
        if (remainingAbsolute <= 0) throw new BizException(ErrorType.UNAUTHORIZED, "登录会话已达到最长有效期");
        long refreshTtlMs = Math.min(jwtRefreshExpiration, remainingAbsolute);
        return generateLoginSession(user, session.startedAtEpochMs(), refreshTtlMs);
    }

    private IssuedAuthSession generateLoginSession(User user, long startedAtEpochMs) {
        if (user == null || Boolean.FALSE.equals(user.getEnabled())) throw new BizException(ErrorType.UNAUTHORIZED, "账号不可用");
        return generateLoginSession(user, startedAtEpochMs, jwtRefreshExpiration);
    }

    private IssuedAuthSession generateLoginSession(User user, long startedAtEpochMs, long refreshTtlMs) {
        String accessToken = jwtTokenProvider.generateToken(user.getId(), user.getRole());
        String accessHash = org.apache.commons.codec.digest.DigestUtils.sha256Hex(accessToken);
        redisUtil.set(RedisKeys.TOKEN + accessHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);
        redisUtil.sadd(RedisKeys.ACTIVE_TOKENS + user.getId(), accessHash);
        String refreshToken = generateRefreshToken();
        sessionStore.saveRefresh(refreshToken, user.getId(), startedAtEpochMs, refreshTtlMs);
        return new IssuedAuthSession(new top.zhaizz.pojo.vo.auth.LoginVO(accessToken, UserConverter.toUserVO(user)), refreshToken,
                Math.max(1, refreshTtlMs / 1000));
    }

    private String generateRefreshToken() {
        byte[] bytes = new byte[32];
        SECURE_RANDOM.nextBytes(bytes);
        StringBuilder result = new StringBuilder(64);
        for (byte b : bytes) result.append(String.format("%02x", b & 0xFF));
        return result.toString();
    }

    @Override
    public void forgotPassword(String email) {
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getEmail, email));
        if (user != null) verificationService.sendPasswordResetCode(email);
    }

    @Override
    public void resetPassword(ResetPasswordDTO request) {
        verificationService.verifyPasswordResetCode(request.getEmail(), request.getCode());
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getEmail, request.getEmail()));
        if (user == null) throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now(clock));
        userMapper.updateById(user);
        sessionStore.revokeAll(user.getId());
        redisUtil.del(RedisKeys.PASSWORD_RESET + request.getEmail());
    }
}