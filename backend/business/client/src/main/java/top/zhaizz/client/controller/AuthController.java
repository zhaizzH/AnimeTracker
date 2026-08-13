package top.zhaizz.client.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.AuthService;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.ratelimit.RateLimit;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.security.JwtAuthenticationFilter;
import top.zhaizz.pojo.dto.auth.ForgotPasswordDTO;
import top.zhaizz.pojo.dto.auth.LoginDTO;
import top.zhaizz.pojo.dto.auth.RefreshTokenDTO;
import top.zhaizz.pojo.dto.auth.RegisterDTO;
import top.zhaizz.pojo.dto.auth.ResendCodeDTO;
import top.zhaizz.pojo.dto.auth.ResetPasswordDTO;
import top.zhaizz.pojo.dto.auth.VerifyEmailDTO;
import top.zhaizz.pojo.vo.auth.LoginVO;

/**
 * 认证控制器
 */
@RestController
@RequestMapping("/api/client/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * 用户注册
     * <p>创建用户并发送验证码邮件，注册成功后需调用 verify-email 完成验证</p>
     */
    // 注册防刷：同一 IP 5 分钟最多 10 次
    @RateLimit(@RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 10, windowSeconds = 300))
    @OperationLog(action = OperationLogConstants.ACTION_REGISTER, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterDTO request) {
        authService.register(request);
        return Result.success(null);
    }

    /**
     * 验证邮箱
     * <p>校验验证码，通过后标记邮箱已验证并返回 JWT Token 和用户信息</p>
     */
    @OperationLog(action = OperationLogConstants.ACTION_VERIFY_EMAIL, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/verify-email")
    public Result<LoginVO> verifyEmail(@Valid @RequestBody VerifyEmailDTO request) {
        LoginVO loginVO = authService.verifyEmail(request.getEmail(), request.getCode());
        return Result.success(loginVO);
    }

    /**
     * 重新发送验证码（验证码邮件未收到或已过期时重发）
     */
    // 验证码防刷：同一邮箱 60 秒 1 次、同一 IP 60 秒 5 次
    @RateLimit({
            @RateLimit.Rule(key = RateLimit.LimitKey.EMAIL, limit = 1, windowSeconds = 60),
            @RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 5, windowSeconds = 60)
    })
    @PostMapping("/resend-code")
    public Result<Void> resendCode(@Valid @RequestBody ResendCodeDTO request) {
        authService.resendCode(request.getEmail());
        return Result.success(null);
    }

    /**
     * 用户登录（邮箱已验证，支持用户名或邮箱 + 密码）
     */
    @OperationLog(action = OperationLogConstants.ACTION_LOGIN, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginDTO request) {
        LoginVO loginVO = authService.login(request);
        return Result.success(loginVO);
    }

    /**
     * 忘记密码 — 发送重置验证码（邮箱不存在时静默成功，防枚举）
     */
    // 验证码防刷：同一邮箱 60 秒 1 次、同一 IP 60 秒 5 次
    @RateLimit({
            @RateLimit.Rule(key = RateLimit.LimitKey.EMAIL, limit = 1, windowSeconds = 60),
            @RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 5, windowSeconds = 60)
    })
    @PostMapping("/forgot-password")
    public Result<Void> forgotPassword(@Valid @RequestBody ForgotPasswordDTO request) {
        authService.forgotPassword(request.getEmail());
        return Result.success(null);
    }

    /**
     * 忘记密码 — 重置密码（验证码校验通过后重置并踢出所有设备）
     */
    @OperationLog(action = OperationLogConstants.ACTION_RESET_PASSWORD, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/reset-password")
    public Result<Void> resetPassword(@Valid @RequestBody ResetPasswordDTO request) {
        authService.resetPassword(request);
        return Result.success(null);
    }

    /**
     * 刷新 Token
     * <p>使用 Refresh Token 换取新的 Access Token + Refresh Token（轮换）</p>
     */
    @PostMapping("/refresh")
    public Result<LoginVO> refresh(@Valid @RequestBody RefreshTokenDTO request) {
        LoginVO loginVO = authService.refresh(request.getRefreshToken());
        return Result.success(loginVO);
    }

    /**
     * 用户退出登录（当前 token 立即失效）
     */
    @OperationLog(action = OperationLogConstants.ACTION_LOGOUT, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/logout")
    public Result<Void> logout(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith(JwtAuthenticationFilter.BEARER_PREFIX)) {
            String token = authHeader.substring(JwtAuthenticationFilter.BEARER_PREFIX.length());
            authService.logout(token);
        }
        return Result.success(null);
    }
}
