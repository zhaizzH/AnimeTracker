package top.zhaizz.client.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.pojo.dto.auth.IssuedAuthSession;
import top.zhaizz.client.service.AuthService;
import top.zhaizz.client.service.RefreshCookieService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.log.constant.OperationLogConstants;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.log.annotation.OperationLog;
import top.zhaizz.infrastructure.ratelimit.RateLimit;
import top.zhaizz.common.result.Result;
import top.zhaizz.auth.security.JwtAuthenticationFilter;
import top.zhaizz.pojo.dto.auth.*;
import top.zhaizz.pojo.vo.auth.LoginVO;

/** AuthController HTTP 控制器 */
@RestController
@RequestMapping("/api/client/auth")
@RequiredArgsConstructor
public class AuthController {
    /** 用户认证业务服务 */
    private final AuthService authService;
    /** refresh Cookie 写入与清理服务 */
    private final RefreshCookieService refreshCookieService;

    /**
     * 注册账户并发送邮箱验证码
     * @param request 注册用户名、邮箱与密码
     * @return 无数据的统一成功响应
     */
    @RateLimit(@RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 10, windowSeconds = 300))
    @OperationLog(action = OperationLogConstants.ACTION_REGISTER, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterDTO request) {
        authService.register(request);
        return Result.success(null);
    }

    /**
     * 验证邮箱并写入刷新 Cookie
     * @param request 邮箱地址及验证码
     * @param response 用于写入 Cookie 的 HTTP 响应
     * @return 包含访问令牌和用户信息的登录响应
     */
    @OperationLog(action = OperationLogConstants.ACTION_VERIFY_EMAIL, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/verify-email")
    public Result<LoginVO> verifyEmail(@Valid @RequestBody VerifyEmailDTO request, HttpServletResponse response) {
        return issue(authService.verifyEmail(request.getEmail(), request.getCode()), response);
    }

    /**
     * 重新发送邮箱验证码
     * @param request 待重新发送验证码的邮箱
     * @return 无数据的统一成功响应
     */
    @RateLimit({@RateLimit.Rule(key = RateLimit.LimitKey.EMAIL, limit = 1, windowSeconds = 60), @RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 5, windowSeconds = 60)})
    @PostMapping("/resend-code")
    public Result<Void> resendCode(@Valid @RequestBody ResendCodeDTO request) {
        authService.resendCode(request.getEmail());
        return Result.success(null);
    }

    /**
     * 校验账户并写入刷新 Cookie
     * @param request 登录用户名或邮箱及密码
     * @param response 用于写入 Cookie 的 HTTP 响应
     * @return 包含访问令牌和用户信息的登录响应
     */
    @OperationLog(action = OperationLogConstants.ACTION_LOGIN, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginDTO request, HttpServletResponse response) {
        return issue(authService.login(request), response);
    }

    /**
     * 申请密码重置验证码
     * @param request 申请重置密码的邮箱
     * @return 无数据的统一成功响应
     */
    @RateLimit({@RateLimit.Rule(key = RateLimit.LimitKey.EMAIL, limit = 1, windowSeconds = 60), @RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 5, windowSeconds = 60)})
    @PostMapping("/forgot-password")
    public Result<Void> forgotPassword(@Valid @RequestBody ForgotPasswordDTO request) {
        authService.forgotPassword(request.getEmail());
        return Result.success(null);
    }

    /**
     * 重置密码并清除刷新 Cookie
     * @param request 邮箱、验证码及新密码
     * @param response 用于写入 Cookie 的 HTTP 响应
     * @return 无数据的统一成功响应
     */
    @OperationLog(action = OperationLogConstants.ACTION_RESET_PASSWORD, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/reset-password")
    public Result<Void> resetPassword(@Valid @RequestBody ResetPasswordDTO request, HttpServletResponse response) {
        authService.resetPassword(request);
        refreshCookieService.clear(response);
        return Result.success(null);
    }

    /**
     * 轮换登录会话，认证失败时清除刷新 Cookie
     * @param refreshToken 客户端刷新令牌
     * @param response 用于写入 Cookie 的 HTTP 响应
     * @return 包含新访问令牌和用户信息的登录响应
     */
    @PostMapping("/refresh")
    public Result<LoginVO> refresh(@CookieValue(value = "at_refresh", required = false) String refreshToken,
                                   HttpServletResponse response) {
        try {
            return issue(authService.refresh(refreshToken), response);
        } catch (BizException e) {
            if (e.getCode() == ErrorType.UNAUTHORIZED.getCode() || e.getCode() == ErrorType.FORBIDDEN.getCode()) {
                refreshCookieService.clear(response);
            }
            throw e;
        }
    }

    /**
     * 撤销登录凭据并清除刷新 Cookie
     * @param request 读取访问令牌的当前 HTTP 请求
     * @param response 用于写入 Cookie 的 HTTP 响应
     * @param refreshToken 客户端刷新令牌
     * @return 无数据的统一成功响应
     */
    @OperationLog(action = OperationLogConstants.ACTION_LOGOUT, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/logout")
    public Result<Void> logout(HttpServletRequest request, HttpServletResponse response,
                               @CookieValue(value = "at_refresh", required = false) String refreshToken) {
        String accessToken = null;
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith(JwtAuthenticationFilter.BEARER_PREFIX)) {
            accessToken = authHeader.substring(JwtAuthenticationFilter.BEARER_PREFIX.length());
        }
        authService.logout(accessToken, refreshToken);
        refreshCookieService.clear(response);
        return Result.success(null);
    }

    /**
     * 写入刷新 Cookie 并包装登录响应体
     *
     * @param issued 已签发的登录会话
     * @param response 当前 HTTP 响应
     * @return 包含登录信息的统一成功结果
     */
    private Result<LoginVO> issue(IssuedAuthSession issued, HttpServletResponse response) {
        refreshCookieService.add(response, issued.refreshToken(), issued.refreshMaxAgeSeconds());
        return Result.success(issued.body());
    }
}
