package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.auth.LoginDTO;
import top.zhaizz.pojo.dto.auth.RegisterDTO;
import top.zhaizz.pojo.dto.auth.ResetPasswordDTO;
import top.zhaizz.pojo.vo.auth.LoginVO;

/**
 * 认证服务接口
 */
public interface AuthService {

    /**
     * 用户注册
     * <p>创建用户（email_verified=false）并发送验证码邮件</p>
     */
    void register(RegisterDTO request);

    /**
     * 重新发送验证码
     */
    void resendCode(String email);

    /**
     * 验证邮箱
     * <p>校验验证码通过后标记邮箱已验证并返回 JWT</p>
     */
    LoginVO verifyEmail(String email, String code);

    /**
     * 用户登录
     */
    LoginVO login(LoginDTO request);

    /**
     * 用户注销
     */
    void logout(String token);

    /**
     * 刷新 Token
     */
    LoginVO refresh(String refreshToken);

    /**
     * 忘记密码 — 发送重置验证码
     * <p>邮箱不存在时静默返回成功（防枚举）</p>
     */
    void forgotPassword(String email);

    /**
     * 重置密码
     * <p>验证码校验通过后更新密码，踢出所有设备（删除全部活跃 token）</p>
     */
    void resetPassword(ResetPasswordDTO request);
}
