package top.zhaizz.animetracker.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.animetracker.common.exception.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.common.util.RedisClient;
import top.zhaizz.animetracker.user.converter.UserConverter;
import top.zhaizz.animetracker.common.dto.LoginDTO;
import top.zhaizz.animetracker.common.dto.RegisterDTO;
import top.zhaizz.animetracker.common.entity.User;
import top.zhaizz.animetracker.user.mapper.UserMapper;
import top.zhaizz.animetracker.user.service.AuthService;
import top.zhaizz.animetracker.common.vo.LoginVO;
import top.zhaizz.animetracker.common.vo.UserVO;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.Date;

/**
 * 认证服务实现
 */
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final RedisClient redisClient;

    @Value("${jwt.secret}")
    private String jwtSecret;   // JWT 密钥

    @Value("${jwt.expiration}")
    private long jwtExpiration; // 过期时间，单位毫秒

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

        // 2. 生成 JWT
        String token = generateToken(user.getId(), user.getRole());

        // 3. 保存信息到 Redis
        redisClient.set("Authorization:Bearer " + token, user.getId().toString());

        // 4. 返回 Token + 用户信息
        return new LoginVO(token, UserConverter.toUserVO(user));
    }

    @Override
    public Void logout() {
        // 1. 查找用户

        // TODO 实现redis功能
        // 2.从请求头获取 token

        // 3. 从 Redis 中删除

        // 4. 返回成功
        return null;
    }

    @Override
    public String generateToken(Long userId, String role) {
        SecretKey secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
        Date now = new Date();
        Date expiry = new Date(now.getTime() + jwtExpiration);

        return Jwts.builder()
                .claim("userId", userId)
                .claim("role", role)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(secretKey, SignatureAlgorithm.HS256)
                .compact();
    }
}
