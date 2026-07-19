package top.zhaizz.user.service;

/**
 * 邮箱验证服务：验证码生成、发送、校验
 */
public interface VerificationService {

    /**
     * 生成验证码并发送到指定邮箱
     *
     * @param email 目标邮箱
     * @throws top.zhaizz.common.exception.BizException 当发送失败时抛出
     */
    void sendVerificationCode(String email);

    /**
     * 校验邮箱验证码
     * <p>校验成功后标记 user.email_verified = true</p>
     *
     * @param email 邮箱
     * @param code  用户输入的验证码
     * @throws top.zhaizz.common.exception.BizException 验证码过期或错误时抛出
     */
    void verifyEmail(String email, String code);

    /**
     * 发送邮箱修改验证码（检查新邮箱唯一性）
     *
     * @param userId   当前用户 ID
     * @param newEmail 新邮箱
     */
    void sendEmailChangeCode(Long userId, String newEmail);

    /**
     * 校验邮箱修改验证码
     * <p>校验成功后更新 email、email_verified=true，发送通知到旧邮箱</p>
     *
     * @param userId   当前用户 ID
     * @param newEmail 新邮箱
     * @param code     用户输入的验证码
     */
    void verifyEmailChangeCode(Long userId, String newEmail, String code);
}
