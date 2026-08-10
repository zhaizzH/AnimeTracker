package top.zhaizz.client.service.impl;

import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.security.JwtTokenProvider;
import top.zhaizz.common.util.RedisKeys;
import top.zhaizz.common.util.RedisUtil;
import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.entity.User;

import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AuthServiceImplTest {

    private final UserMapper userMapper = mock(UserMapper.class);
    private final PasswordEncoder passwordEncoder = mock(PasswordEncoder.class);
    private final RedisUtil redisUtil = mock(RedisUtil.class);
    private final JwtTokenProvider jwtTokenProvider = mock(JwtTokenProvider.class);
    private final VerificationService verificationService = mock(VerificationService.class);
    private final AuthServiceImpl service = new AuthServiceImpl(userMapper, passwordEncoder, redisUtil, jwtTokenProvider, verificationService);

    private static final String USERNAME = "alice";
    private static final String FAIL_KEY = RedisKeys.LOGIN_FAIL + USERNAME;

    private LoginDTO loginDTO() {
        LoginDTO dto = new LoginDTO();
        dto.setUsername(USERNAME);
        dto.setPassword("whatever");
        return dto;
    }

    @Test
    void locksAccountAfterFiveFailedAttempts() {
        // 纯 mockito 构造的 service 未注入 @Value 字段，这里手动赋默认配置值 5
        ReflectionTestUtils.setField(service, "LOGIN_FAIL_WINDOW_MINUTES", 5L);

        User user = new User();
        user.setPassword("encoded");
        when(userMapper.selectOne(any())).thenReturn(user);
        when(passwordEncoder.matches(any(), any())).thenReturn(false);

        // 前 5 次错误密码 → 401，并逐次递增失败计数
        for (int i = 0; i < 5; i++) {
            assertThatThrownBy(() -> service.login(loginDTO()))
                    .isInstanceOf(BizException.class)
                    .extracting(e -> ((BizException) e).getCode())
                    .isEqualTo(ErrorType.UNAUTHORIZED.getCode());
        }
        verify(redisUtil, times(5)).incr(eq(FAIL_KEY), eq(5L), eq(TimeUnit.MINUTES));

        // 第 6 次起即使密码正确也被锁定（锁定检查在密码校验之前）
        when(redisUtil.get(FAIL_KEY)).thenReturn("5");
        when(passwordEncoder.matches(any(), any())).thenReturn(true);
        assertThatThrownBy(() -> service.login(loginDTO()))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.UNAUTHORIZED.getCode());
    }
}
