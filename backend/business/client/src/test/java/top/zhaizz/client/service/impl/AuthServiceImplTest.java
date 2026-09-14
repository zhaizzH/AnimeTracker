package top.zhaizz.client.service.impl;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;
import top.zhaizz.auth.security.AuthSessionStore;
import top.zhaizz.auth.security.AuthTokenService;
import top.zhaizz.client.constant.ClientRedisKeys;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.infrastructure.redis.RedisUtil;
import top.zhaizz.pojo.dto.auth.*;
import top.zhaizz.pojo.entity.User;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;

/** 登录资格校验、刷新消费顺序和注销撤销的业务编排回归。 */
class AuthServiceImplTest {
    /** 固定首次登录时刻，单位为纪元毫秒。 */
    private static final long NOW = 1_800_000_000_000L;
    /** 模拟账户持久化。 */
    private final UserMapper users = mock(UserMapper.class);
    /** 模拟密码哈希校验。 */
    private final PasswordEncoder passwords = mock(PasswordEncoder.class);
    /** 模拟登录失败计数。 */
    private final RedisUtil redis = mock(RedisUtil.class);
    /** 模拟认证凭据签发。 */
    private final AuthTokenService tokens = mock(AuthTokenService.class);
    /** 模拟邮箱验证业务。 */
    private final VerificationService verification = mock(VerificationService.class);
    /** 模拟刷新原子消费与撤销。 */
    private final AuthSessionStore sessions = mock(AuthSessionStore.class);
    /** 被测用户端认证编排。 */
    private final AuthServiceImpl service = new AuthServiceImpl(users, passwords, redis, tokens, verification, sessions);

    /** 配置固定时钟与失败计数窗口，避免测试依赖运行时间。 */
    @BeforeEach
    void configure() {
        ReflectionTestUtils.setField(service, "clock", Clock.fixed(Instant.ofEpochMilli(NOW), ZoneOffset.UTC));
        ReflectionTestUtils.setField(service, "maxLoginFails", 5);
        ReflectionTestUtils.setField(service, "loginFailWindowMinutes", 5L);
    }

    /** 成功登录清除失败计数，并以当前时刻签发首次会话。 */
    @Test
    void loginIssuesFirstSession() {
        User user = user();
        when(users.selectOne(any())).thenReturn(user);
        when(passwords.matches("password", "hash")).thenReturn(true);
        when(tokens.issue(7L, "USER", NOW, false)).thenReturn(new AuthTokens("access", "refresh", 90L));
        IssuedAuthSession result = service.login(login());
        assertThat(result.body().getToken()).isEqualTo("access");
        assertThat(result.body().getUser().getId()).isEqualTo(7L);
        assertThat(result.refreshToken()).isEqualTo("refresh");
        assertThat(result.refreshMaxAgeSeconds()).isEqualTo(90L);
        verify(redis).del(ClientRedisKeys.LOGIN_FAIL + "alice");
        verify(tokens).issue(7L, "USER", NOW, false);
    }

    /** 密码错误累加限时计数且不签发凭据。 */
    @Test
    void wrongPasswordIncrementsFailures() {
        when(users.selectOne(any())).thenReturn(user());
        assertThatThrownBy(() -> service.login(login())).isInstanceOf(BizException.class).hasMessage("用户名或密码错误");
        verify(redis).incr(ClientRedisKeys.LOGIN_FAIL + "alice", 5L, TimeUnit.MINUTES);
        verifyNoInteractions(tokens);
    }

    /** 达到失败阈值时在查询账户之前拒绝登录。 */
    @Test
    void lockedLoginSkipsAccountLookup() {
        when(redis.get(ClientRedisKeys.LOGIN_FAIL + "alice")).thenReturn("5");
        assertThatThrownBy(() -> service.login(login())).isInstanceOf(BizException.class).hasMessageContaining("次数过多");
        verifyNoInteractions(users, passwords, tokens);
    }

    /** 禁用账户即使密码正确也不能取得凭据。 */
    @Test
    void disabledAccountCannotLogin() {
        User user = user(); user.setEnabled(false);
        when(users.selectOne(any())).thenReturn(user);
        when(passwords.matches("password", "hash")).thenReturn(true);
        assertThatThrownBy(() -> service.login(login())).isInstanceOf(BizException.class).hasMessage("账号不可用");
        verifyNoInteractions(tokens);
    }

    /** 未验证邮箱返回验证所需邮箱信息，禁止签发登录凭据。 */
    @Test
    void unverifiedAccountCannotLogin() {
        User user = user(); user.setEmailVerified(false);
        when(users.selectOne(any())).thenReturn(user);
        when(passwords.matches("password", "hash")).thenReturn(true);
        BizException error = catchThrowableOfType(() -> service.login(login()), BizException.class);
        assertThat(error.getCode()).isEqualTo(ErrorType.EMAIL_NOT_VERIFIED.getCode());
        assertThat(error.getData()).isEqualTo(java.util.Map.of("email", "alice@example.test"));
        verifyNoInteractions(tokens);
    }

    /** 刷新先消费旧凭据再查账户，续签沿用原始起点而非当前时刻。 */
    @Test
    void refreshPreservesAbsoluteSessionStartAndRejectsReuse() {
        long originalStart = NOW - 60_000L;
        when(sessions.consumeRefresh("old")).thenReturn(Optional.of(new ConsumedRefreshSession(7L, originalStart)), Optional.empty());
        when(users.selectById(7L)).thenReturn(user());
        when(tokens.issue(7L, "USER", originalStart, true)).thenReturn(new AuthTokens("new-access", "new-refresh", 30L));
        IssuedAuthSession result = service.refresh("old");
        assertThat(result.refreshToken()).isEqualTo("new-refresh");
        assertThat(result.refreshMaxAgeSeconds()).isEqualTo(30L);
        var order = inOrder(sessions, users, tokens);
        order.verify(sessions).consumeRefresh("old");
        order.verify(users).selectById(7L);
        order.verify(tokens).issue(7L, "USER", originalStart, true);
        assertThatThrownBy(() -> service.refresh("old")).isInstanceOf(BizException.class).hasMessageContaining("无效或已过期");
        verify(tokens, times(1)).issue(anyLong(), anyString(), anyLong(), anyBoolean());
        verify(users, times(1)).selectById(7L);
    }

    /** 刷新消费后发现账户禁用时拒绝续签。 */
    @Test
    void disabledAccountCannotRefresh() {
        when(sessions.consumeRefresh("old")).thenReturn(Optional.of(new ConsumedRefreshSession(7L, NOW - 1000)));
        User user = user(); user.setEnabled(false);
        when(users.selectById(7L)).thenReturn(user);
        assertThatThrownBy(() -> service.refresh("old")).isInstanceOf(BizException.class).hasMessage("账号不可用");
        verify(sessions).consumeRefresh("old");
        verifyNoInteractions(tokens);
    }

    /** 达到绝对寿命时原样传播认证拒绝，不返回半成品登录结果。 */
    @Test
    void absoluteExpiryFailsRefresh() {
        long originalStart = NOW - 60_000L;
        when(sessions.consumeRefresh("old")).thenReturn(Optional.of(new ConsumedRefreshSession(7L, originalStart)));
        when(users.selectById(7L)).thenReturn(user());
        BizException expired = new BizException(ErrorType.UNAUTHORIZED, "会话已过期");
        when(tokens.issue(7L, "USER", originalStart, true)).thenThrow(expired);
        assertThatThrownBy(() -> service.refresh("old")).isSameAs(expired);
    }

    /** 缺失刷新凭据直接拒绝，不访问会话或账户存储。 */
    @Test
    void absentRefreshSkipsStores() {
        assertThatThrownBy(() -> service.refresh(null)).isInstanceOf(BizException.class);
        assertThatThrownBy(() -> service.refresh(" ")).isInstanceOf(BizException.class);
        verifyNoInteractions(sessions, users, tokens);
    }

    /** 注销分别撤销访问和刷新凭据，空值及空白不触发撤销。 */
    @Test
    void logoutRevokesOnlyProvidedTokens() {
        service.logout("access", "refresh");
        verify(sessions).revokeAccess("access");
        verify(sessions).revokeRefresh("refresh");
        service.logout(null, " ");
        service.logout(" ", null);
        verifyNoMoreInteractions(sessions);
        verifyNoInteractions(tokens, users);
    }

    /**
     * 创建可登录账户。
     * @return 已验证邮箱且未禁用的普通用户
     */
    private static User user() {
        User user = new User(); user.setId(7L); user.setUsername("alice"); user.setPassword("hash");
        user.setEmail("alice@example.test"); user.setRole("USER"); user.setEmailVerified(true); user.setEnabled(true);
        return user;
    }

    /**
     * 创建用户名密码登录请求。
     * @return 与模拟密码匹配的登录输入
     */
    private static LoginDTO login() {
        LoginDTO request = new LoginDTO(); request.setUsername("alice"); request.setPassword("password"); return request;
    }
}
