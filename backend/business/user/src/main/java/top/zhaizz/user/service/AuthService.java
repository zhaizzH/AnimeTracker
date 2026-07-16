package top.zhaizz.user.service;

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
     *
     * @param email 邮箱地址
     * @param code  验证码
     * @return LoginVO（含 JWT Token 和用户信息）
     */
    LoginVO verifyEmail(String email, String code);

    /**
     * 用户登录
     * @return LoginVO（含 JWT Token 和用户信息）
     */
    LoginVO login(LoginDTO request);

    /**
     * 用户注销
     */
    void logout(String token);

    /**
     * 生成 JWT Token
     */
    String generateToken(Long userId, String role);
}
