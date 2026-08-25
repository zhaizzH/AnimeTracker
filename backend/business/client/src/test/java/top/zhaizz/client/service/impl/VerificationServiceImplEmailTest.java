package top.zhaizz.client.service.impl;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.client.gateway.EmailGateway;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.constant.RedisKeys;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ratelimit.RateLimiter;
import top.zhaizz.common.util.RedisUtil;

import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class VerificationServiceImplEmailTest {
    @Mock RedisUtil redisUtil;
    @Mock UserMapper userMapper;
    @Mock EmailGateway emailGateway;
    @Mock RateLimiter rateLimiter;

    private VerificationServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new VerificationServiceImpl(redisUtil, userMapper, emailGateway, rateLimiter);
    }

    @Test
    void verificationCodeIsStoredThenSentThroughGateway() {
        service.sendVerificationCode("user@example.com");

        ArgumentCaptor<String> code = ArgumentCaptor.forClass(String.class);
        verify(redisUtil).set(eq(RedisKeys.EMAIL + "user@example.com"),
                code.capture(), eq(5L), eq(TimeUnit.MINUTES));
        verify(emailGateway).send(
                eq("user@example.com"),
                eq("[AnimeTracker] 邮箱验证码"),
                eq("你的验证码是：" + code.getValue() + "\n\n此验证码5分钟内有效，请勿泄露给他人。"));
    }

    @Test
    void deliveryFailureDeletesStoredCodeAndReturnsGenericBusinessError() {
        doThrow(new IllegalStateException("private resend failure"))
                .when(emailGateway).send(eq("user@example.com"), anyString(), anyString());

        BizException error = assertThrows(BizException.class,
                () -> service.sendVerificationCode("user@example.com"));

        assertThat(error.getCode()).isEqualTo(ErrorType.INTERNAL_ERROR.getCode());
        assertThat(error.getMessage()).isEqualTo("验证码发送失败，请稍后重试");
        assertThat(error.getMessage()).doesNotContain("private resend failure");
        verify(redisUtil).del(RedisKeys.EMAIL + "user@example.com");
    }
}
