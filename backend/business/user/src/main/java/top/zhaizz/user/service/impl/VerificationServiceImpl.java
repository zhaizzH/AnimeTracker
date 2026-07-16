package top.zhaizz.user.service.impl;

import com.resend.Resend;
import com.resend.core.exception.ResendException;
import com.resend.services.emails.model.CreateEmailOptions;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.util.RedisClient;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.user.mapper.UserMapper;
import top.zhaizz.user.service.VerificationService;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

/**
 * 邮箱验证服务实现
 */
@Service
@RequiredArgsConstructor
public class VerificationServiceImpl implements VerificationService {

    private final RedisClient redisClient;
    private final UserMapper userMapper;

    @Value("${resend.api-key}")
    private String resendApiKey;

    private static final String REDIS_KEY_PREFIX = "auth:email:";
    private static final long CODE_TTL_MINUTES = 5;
    private static final int CODE_LENGTH = 6;
    private static final String ALPHANUMERIC = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
    private static final SecureRandom RANDOM = new SecureRandom();

    @Override
    public void sendVerificationCode(String email) {
        // 1. 生成6位字母数字验证码（排除易混淆字符 0/O/1/l/I）
        StringBuilder code = new StringBuilder(CODE_LENGTH);
        for (int i = 0; i < CODE_LENGTH; i++) {
            code.append(ALPHANUMERIC.charAt(RANDOM.nextInt(ALPHANUMERIC.length())));
        }

        // 2. 存入 Redis（5分钟 TTL）
        redisClient.set(REDIS_KEY_PREFIX + email, code.toString(), CODE_TTL_MINUTES, TimeUnit.MINUTES);

        // 3. 通过 Resend 发送邮件
        Resend resend = new Resend(resendApiKey);
        CreateEmailOptions params = CreateEmailOptions.builder()
                .from("admin@zhaizz.top")
                .to(email)
                .subject("[AnimeTracker] 邮箱验证码")
                .text("你的验证码是：" + code + "\n\n此验证码5分钟内有效，请勿泄露给他人。")
                .build();

        try {
            resend.emails().send(params);
        } catch (ResendException e) {
            // 发送失败时清理 Redis 中的验证码
            redisClient.del(REDIS_KEY_PREFIX + email);
            throw new BizException(ErrorType.INTERNAL_ERROR, "验证码发送失败，请稍后重试");
        }
    }

    @Override
    public void verifyEmail(String email, String code) {
        // 1. 从 Redis 获取存储的验证码
        String storedCode = redisClient.get(REDIS_KEY_PREFIX + email);

        if (storedCode == null) {
            throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码已过期，请重新发送");
        }

        if (!storedCode.equals(code)) {
            throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码不正确");
        }

        // 2. 校验通过，删除 Redis key
        redisClient.del(REDIS_KEY_PREFIX + email);

        // 3. 更新用户 email_verified 状态
        User user = userMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<User>()
                        .eq(User::getEmail, email)
        );
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }
        user.setEmailVerified(true);
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);
    }
}
