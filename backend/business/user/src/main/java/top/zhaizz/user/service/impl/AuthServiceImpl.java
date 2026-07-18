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

import java.time.LocalDateTime;
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

    private static final String REDIS_TOKEN_PREFIX = "auth:token:";

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
        // 1. 查找用户
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getUsername, request.getUsername())
        );

        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ErrorType.UNAUTHORIZED, "用户名或密码错误");
        }

        return generateLoginVO(user);
    }

    @Override
    public void logout(String token) {
        // 计算 SHA256 摘要，从 Redis 删除
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.del(REDIS_TOKEN_PREFIX + tokenHash);
    }

    /**
     * 生成 JWT Token 并存入 Redis 白名单，返回 LoginVO
     */
    private LoginVO generateLoginVO(User user) {
        String token = jwtTokenProvider.generateToken(user.getId(), user.getRole());
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.set(REDIS_TOKEN_PREFIX + tokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);
        return new LoginVO(token, UserConverter.toUserVO(user));
    }
}
