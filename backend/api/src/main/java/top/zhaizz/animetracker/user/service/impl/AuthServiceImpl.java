package top.zhaizz.animetracker.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.animetracker.common.exception.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.common.util.RedisClient;
import top.zhaizz.animetracker.security.JwtTokenProvider;
import top.zhaizz.animetracker.user.converter.UserConverter;
import top.zhaizz.animetracker.common.dto.LoginDTO;
import top.zhaizz.animetracker.common.dto.RegisterDTO;
import top.zhaizz.animetracker.common.entity.User;
import top.zhaizz.animetracker.user.mapper.UserMapper;
import top.zhaizz.animetracker.user.service.AuthService;
import top.zhaizz.animetracker.common.vo.LoginVO;
import top.zhaizz.animetracker.common.vo.UserVO;

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

    @Value("${jwt.expiration}")
    private long jwtExpiration; // 过期时间，单位毫秒

    private static final String REDIS_TOKEN_PREFIX = "auth:token:";

    @Override
    public UserVO register(RegisterDTO request) {
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
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());

        // 3. 保存
        userMapper.insert(user);

        return UserConverter.toUserVO(user);
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

        // 2. 生成 JWT（统一使用 JwtTokenProvider）
        String token = jwtTokenProvider.generateToken(user.getId(), user.getRole());

        // 3. 计算 SHA256 摘要，存入 Redis（带 TTL）
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.set(REDIS_TOKEN_PREFIX + tokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);

        // 4. 返回 Token + 用户信息
        return new LoginVO(token, UserConverter.toUserVO(user));
    }

    @Override
    public void logout(String token) {
        // 计算 SHA256 摘要，从 Redis 删除
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.del(REDIS_TOKEN_PREFIX + tokenHash);
    }

    @Override
    public String generateToken(Long userId, String role) {
        // 委派给 JwtTokenProvider（兼容旧调用者）
        return jwtTokenProvider.generateToken(userId, role);
    }
}
