package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.auth.IssuedAuthSession;
import top.zhaizz.pojo.dto.auth.LoginDTO;
import top.zhaizz.pojo.dto.auth.RegisterDTO;
import top.zhaizz.pojo.dto.auth.ResetPasswordDTO;

/** AuthService 业务服务 */
public interface AuthService {
    /**
     * 注册用户并发送邮箱验证验证码
     *
     * @param request 用户注册信息
     * @throws top.zhaizz.common.exception.BizException 用户名或邮箱已存在，或验证码发送失败
     */
    void register(RegisterDTO request);
    /**
     * 为未验证邮箱重新发送验证码
     *
     * @param email 待验证邮箱
     * @throws top.zhaizz.common.exception.BizException 邮箱不存在、已验证或发送失败
     */
    void resendCode(String email);
    /**
     * 校验邮箱验证码并签发登录会话
     *
     * @param email 待验证邮箱
     * @param code 邮箱验证码
     * @return 登录响应和刷新 Cookie 所需的会话信息
     * @throws top.zhaizz.common.exception.BizException 验证码无效或用户不存在
     */
    IssuedAuthSession verifyEmail(String email, String code);
    /**
     * 校验账户凭据并签发登录会话
     *
     * @param request 用户名或邮箱及密码
     * @return 登录响应和刷新 Cookie 所需的会话信息
     * @throws top.zhaizz.common.exception.BizException 凭据错误、账户禁用或未验证邮箱
     */
    IssuedAuthSession login(LoginDTO request);
    /**
     * 撤销当前访问令牌和刷新会话
     *
     * @param accessToken 访问令牌，可为空
     * @param refreshToken 刷新令牌，可为空
     */
    void logout(String accessToken, String refreshToken);
    /**
     * 原子消费刷新令牌并签发新的登录会话
     *
     * @param refreshToken 刷新令牌
     * @return 新登录响应和刷新 Cookie 所需的会话信息
     * @throws top.zhaizz.common.exception.BizException 令牌无效、过期、重复使用或账户不可用
     */
    IssuedAuthSession refresh(String refreshToken);
    /**
     * 向账户邮箱发送密码重置验证码
     *
     * @param email 账户邮箱
     * @throws top.zhaizz.common.exception.BizException 发送失败时抛出
     */
    void forgotPassword(String email);
    /**
     * 校验密码重置验证码并更新账户密码
     *
     * @param request 邮箱、验证码和新密码
     * @throws top.zhaizz.common.exception.BizException 验证码无效、账户不存在或更新失败
     */
    void resetPassword(ResetPasswordDTO request);
}
