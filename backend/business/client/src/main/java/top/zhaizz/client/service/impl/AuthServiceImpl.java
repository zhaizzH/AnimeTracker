package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.UserConverter;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.pojo.dto.auth.IssuedAuthSession;
import top.zhaizz.client.service.AuthService;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.client.constant.ClientRedisKeys;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.auth.security.AuthSessionStore;
import top.zhaizz.pojo.dto.auth.ConsumedRefreshSession;
import top.zhaizz.auth.security.AuthTokenService;
import top.zhaizz.pojo.dto.auth.AuthTokens;
import top.zhaizz.infrastructure.redis.RedisUtil;
import top.zhaizz.pojo.dto.auth.LoginDTO;
import top.zhaizz.pojo.dto.auth.RegisterDTO;
import top.zhaizz.pojo.dto.auth.ResetPasswordDTO;
import top.zhaizz.pojo.entity.User;

import java.time.Clock;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

/** 保留注册、登录资格、邮箱验证和密码重置业务，委托 auth 管理凭据。 */
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {
    /** 账户持久化查询与更新入口。 */
    private final UserMapper userMapper;
    /** 密码哈希校验和编码器，不处理明文存储。 */
    private final PasswordEncoder passwordEncoder;
    /** 登录失败计数与业务验证码清理入口。 */
    private final RedisUtil redisUtil;
    /** 仅接收已校验身份的凭据签发能力。 */
    private final AuthTokenService tokenService;
    /** 邮箱及密码重置验证码业务。 */
    private final VerificationService verificationService;
    /** 刷新凭据原子消费与会话撤销入口。 */
    private final AuthSessionStore sessionStore;

    /** 登录失败次数阈值，达到后拒绝登录。 */
        /** 允许连续登录失败的最大次数。 */
    @Value("${jwt.max-login-fails}")
    private int maxLoginFails;
    /** 登录失败计数窗口，单位分钟。 */
        /** 登录失败计数窗口时长，单位分钟。 */
    @Value("${jwt.login-fail-window-minutes}")
    private long loginFailWindowMinutes;

    /** 账户更新时间和首次登录时间使用的 UTC 时钟。 */
    private Clock clock = Clock.systemUTC();

    /**
     * 创建默认 USER 账户并发送邮箱验证码。
     * @param request 注册资料，密码仅以哈希持久化
     * @throws BizException 用户名或邮箱已存在时返回 CONFLICT
     */
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

    /**
     * 重新发送邮箱验证凭据。
     * @param email 验证邮件接收地址
     */
    @Override
    public void resendCode(String email) { verificationService.sendVerificationCode(email); }

    /**
     * 验证邮箱后签发该账户首次登录会话。
     * @param email 待验证邮箱
     * @param code 用户提交的验证码
     * @return 用户响应和刷新 Cookie 材料
     * @throws BizException 验证失败或账户不可用
     */
    @Override
    public IssuedAuthSession verifyEmail(String email, String code) {
        verificationService.verifyEmail(email, code);
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getEmail, email));
        return generateLoginSession(user, clock.millis());
    }

    /**
     * 校验密码、邮箱状态及账户可用性后签发会话。
     * @param request 用户名或邮箱及密码
     * @return 用户响应和刷新 Cookie 材料
     * @throws BizException 失败次数超限、凭据错误、邮箱未验证或账户不可用
     */
    @Override
    public IssuedAuthSession login(LoginDTO request) {
        String failKey = ClientRedisKeys.LOGIN_FAIL + request.getUsername();
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

    /**
     * 撤销提交的访问和刷新凭据，空凭据跳过。
     * @param accessToken 访问令牌，可为空或空白
     * @param refreshToken 刷新凭据，可为空或空白
     */
    @Override
    public void logout(String accessToken, String refreshToken) {
        if (accessToken != null && !accessToken.isBlank()) sessionStore.revokeAccess(accessToken);
        if (refreshToken != null && !refreshToken.isBlank()) sessionStore.revokeRefresh(refreshToken);
    }

    /**
     * 先原子消费刷新凭据，再校验账户并委托认证能力续签。
     * @param refreshToken 刷新 Cookie 凭据
     * @return 保持原始会话起点的新凭据及账户响应
     * @throws BizException 凭据无效、账户不可用或绝对寿命耗尽
     */
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
        return generateLoginSession(user, session.startedAtEpochMs(), true);
    }

    /**
     * 校验账户可用性后签发首次登录凭据。
     * @param user 查出的账户，可为空
     * @param startedAtEpochMs 首次登录 UTC 纪元毫秒
     * @return 用户展示信息及仅用于 Cookie 的刷新凭据
     * @throws BizException 账户不存在或禁用时返回 UNAUTHORIZED
     */
    private IssuedAuthSession generateLoginSession(User user, long startedAtEpochMs) {
        if (user == null || Boolean.FALSE.equals(user.getEnabled())) throw new BizException(ErrorType.UNAUTHORIZED, "账号不可用");
        return generateLoginSession(user, startedAtEpochMs, false);
    }

    /**
     * 将认证能力的凭据和用户端转换结果组合为登录结果。
     * @param user 已通过资格校验的账户
     * @param startedAtEpochMs 原始登录 UTC 纪元毫秒
     * @param refreshing 是否续签已消费的刷新凭据
     * @return 响应体与安全 Cookie 材料
     * @throws BizException 刷新会话达到绝对寿命时拒绝续签
     */
    private IssuedAuthSession generateLoginSession(User user, long startedAtEpochMs, boolean refreshing) {
        AuthTokens tokens = tokenService.issue(user.getId(), user.getRole(), startedAtEpochMs, refreshing);
        return new IssuedAuthSession(new top.zhaizz.pojo.vo.auth.LoginVO(tokens.accessToken(), UserConverter.toUserVO(user)),
                tokens.refreshToken(), tokens.refreshMaxAgeSeconds());
    }

    /**
     * 账户存在时发送重置码，账户不存在时同样正常返回。
     * @param email 用户提交的邮箱
     */
    @Override
    public void forgotPassword(String email) {
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getEmail, email));
        if (user != null) verificationService.sendPasswordResetCode(email);
    }

    /**
     * 验证重置码、更新密码并撤销该用户全部会话。
     * @param request 邮箱、重置码和新密码
     * @throws BizException 验证码无效或账户不存在
     */
    @Override
    public void resetPassword(ResetPasswordDTO request) {
        verificationService.verifyPasswordResetCode(request.getEmail(), request.getCode());
        User user = userMapper.selectOne(new LambdaQueryWrapper<User>().eq(User::getEmail, request.getEmail()));
        if (user == null) throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now(clock));
        userMapper.updateById(user);
        sessionStore.revokeAll(user.getId());
        redisUtil.del(ClientRedisKeys.PASSWORD_RESET + request.getEmail());
    }
}
