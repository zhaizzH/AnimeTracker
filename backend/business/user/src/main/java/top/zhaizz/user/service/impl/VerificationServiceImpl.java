package top.zhaizz.user.service.impl;

import com.resend.Resend;
import com.resend.core.exception.ResendException;
import com.resend.services.emails.model.CreateEmailOptions;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
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
@Slf4j
@Service
@RequiredArgsConstructor
public class VerificationServiceImpl implements VerificationService {

    private final RedisClient redisClient;
    private final UserMapper userMapper;

    @Value("${resend.api-key}")
    private String resendApiKey;

    private static final String REDIS_KEY_PREFIX = "auth:email:";
    private static final String REDIS_EMAIL_CHANGE_PREFIX = "auth:email-change:";
    private static final long CODE_TTL_MINUTES = 5;
    private static final int CODE_LENGTH = 6;
    private static final String ALPHANUMERIC = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
    private static final SecureRandom RANDOM = new SecureRandom();

    private String generateCode() {
        StringBuilder code = new StringBuilder(CODE_LENGTH);
        for (int i = 0; i < CODE_LENGTH; i++) {
            code.append(ALPHANUMERIC.charAt(RANDOM.nextInt(ALPHANUMERIC.length())));
        }
        return code.toString();
    }

    @Override
    public void sendVerificationCode(String email) {
        // 1. 生成6位字母数字验证码（排除易混淆字符 0/O/1/l/I）
        String code = generateCode();

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

    @Override
    public void sendEmailChangeCode(Long userId, String newEmail) {
        newEmail = newEmail.toLowerCase();

        // 1. 检查新邮箱唯一性
        if (userMapper.existsByEmail(newEmail)) {
            throw new BizException(ErrorType.CONFLICT, "该邮箱已被其他账号使用");
        }

        // 2. 生成验证码
        String code = generateCode();

        // 3. 存入 Redis（不同 key 前缀）
        redisClient.set(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail, code.toString(), CODE_TTL_MINUTES, TimeUnit.MINUTES);

        // 4. 通过 Resend 发送邮件
        Resend resend = new Resend(resendApiKey);
        CreateEmailOptions params = CreateEmailOptions.builder()
                .from("admin@zhaizz.top")
                .to(newEmail)
                .subject("[AnimeTracker] 邮箱修改验证码")
                .text("你正在修改邮箱绑定，验证码是：" + code + "\n\n此验证码5分钟内有效，请勿泄露给他人。")
                .build();

        try {
            resend.emails().send(params);
        } catch (ResendException e) {
            redisClient.del(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail);
            throw new BizException(ErrorType.INTERNAL_ERROR, "验证码发送失败，请稍后重试");
        }
    }

    @Override
    @Transactional
    public void verifyEmailChangeCode(Long userId, String newEmail, String code) {
        newEmail = newEmail.toLowerCase();

        // 1. 从 Redis 获取存储的验证码
        String storedCode = redisClient.get(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail);
        if (storedCode == null) {
            throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码已过期，请重新发送");
        }
        if (!storedCode.equals(code)) {
            throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码不正确");
        }

        // 2. 再次检查新邮箱唯一性（防并发注册占用）
        if (userMapper.existsByEmail(newEmail)) {
            throw new BizException(ErrorType.CONFLICT, "该邮箱已被其他账号使用");
        }

        // 3. 校验通过，删除 Redis key
        redisClient.del(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail);

        // 4. 查询当前用户，获取旧邮箱
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }
        String oldEmail = user.getEmail();

        // 5. 更新 email + email_verified
        user.setEmail(newEmail);
        user.setEmailVerified(true);
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);

        // 6. 通知旧邮箱（失败不抛异常，不回滚）
        if (oldEmail != null && !oldEmail.isEmpty()) {
            try {
                Resend resend = new Resend(resendApiKey);
                CreateEmailOptions params = CreateEmailOptions.builder()
                        .from("admin@zhaizz.top")
                        .to(oldEmail)
                        .subject("[AnimeTracker] 邮箱变更通知")
                        .text("你的 AnimeTracker 账号邮箱已变更为：" + newEmail + "\n\n如非本人操作，请立即联系管理员。")
                        .build();
                resend.emails().send(params);
            } catch (ResendException e) {
                // ponytail: 通知失败不干扰主流程，静默记日志
                log.warn("旧邮箱通知发送失败: {}", oldEmail, e);
            }
        }
    }
}
