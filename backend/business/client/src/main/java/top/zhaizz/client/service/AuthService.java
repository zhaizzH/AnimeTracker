package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.pojo.vo.LoginVO;

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

}
