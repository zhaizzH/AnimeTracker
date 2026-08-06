package top.zhaizz.client.service.impl;

import com.resend.Resend;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ratelimit.RateLimiter;
import top.zhaizz.common.util.RedisKeys;
import top.zhaizz.common.util.RedisUtil;
import top.zhaizz.pojo.entity.User;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class VerificationServiceImplTest {

    private final RedisUtil redisUtil = mock(RedisUtil.class);
    private final UserMapper userMapper = mock(UserMapper.class);
    private final Resend resend = mock(Resend.class);
    private final RateLimiter rateLimiter = mock(RateLimiter.class);
    private VerificationServiceImpl service;

    @BeforeEach
    void setUp() {
        // 构造器参数顺序 = 字段声明顺序：RedisUtil, UserMapper, Resend, RateLimiter
        service = new VerificationServiceImpl(redisUtil, userMapper, resend, rateLimiter);
    }

    @Test
    void locksWhenOverAttemptLimit() {
        when(rateLimiter.allowOrCount(anyString(), anyInt(), anyInt())).thenReturn(false);
        assertThatThrownBy(() -> service.verifyEmail("a@b.com", "XXXXXX"))
                .isInstanceOf(BizException.class)
                .satisfies(e -> assertThat(((BizException) e).getCode()).isEqualTo(429));
    }

    @Test
    void resetsFailureCounterOnSuccess() {
        when(rateLimiter.allowOrCount(anyString(), anyInt(), anyInt())).thenReturn(true);
        when(redisUtil.get(RedisKeys.EMAIL + "a@b.com")).thenReturn("abc123");
        User user = new User();
        user.setId(1L);
        when(userMapper.selectOne(any())).thenReturn(user);

        service.verifyEmail("a@b.com", "abc123");

        verify(rateLimiter).reset("verify:email:a@b.com");
    }

    @Test
    void wrongCodeDoesNotResetCounter() {
        when(rateLimiter.allowOrCount(anyString(), anyInt(), anyInt())).thenReturn(true);
        when(redisUtil.get(RedisKeys.EMAIL + "a@b.com")).thenReturn("abc123");

        assertThatThrownBy(() -> service.verifyEmail("a@b.com", "WRONG"))
                .isInstanceOf(BizException.class);
        verify(rateLimiter, never()).reset(anyString());
    }
}
