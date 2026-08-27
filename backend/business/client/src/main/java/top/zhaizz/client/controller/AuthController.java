package top.zhaizz.client.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.model.IssuedAuthSession;
import top.zhaizz.client.service.AuthService;
import top.zhaizz.client.service.RefreshCookieService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.ratelimit.RateLimit;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.security.JwtAuthenticationFilter;
import top.zhaizz.pojo.dto.auth.*;
import top.zhaizz.pojo.vo.auth.LoginVO;

@RestController
@RequestMapping("/api/client/auth")
@RequiredArgsConstructor
public class AuthController {
    private final AuthService authService;
    private final RefreshCookieService refreshCookieService;

    @RateLimit(@RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 10, windowSeconds = 300))
    @OperationLog(action = OperationLogConstants.ACTION_REGISTER, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterDTO request) {
        authService.register(request);
        return Result.success(null);
    }

    @OperationLog(action = OperationLogConstants.ACTION_VERIFY_EMAIL, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/verify-email")
    public Result<LoginVO> verifyEmail(@Valid @RequestBody VerifyEmailDTO request, HttpServletResponse response) {
        return issue(authService.verifyEmail(request.getEmail(), request.getCode()), response);
    }

    @RateLimit({@RateLimit.Rule(key = RateLimit.LimitKey.EMAIL, limit = 1, windowSeconds = 60), @RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 5, windowSeconds = 60)})
    @PostMapping("/resend-code")
    public Result<Void> resendCode(@Valid @RequestBody ResendCodeDTO request) {
        authService.resendCode(request.getEmail());
        return Result.success(null);
    }

    @OperationLog(action = OperationLogConstants.ACTION_LOGIN, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginDTO request, HttpServletResponse response) {
        return issue(authService.login(request), response);
    }

    @RateLimit({@RateLimit.Rule(key = RateLimit.LimitKey.EMAIL, limit = 1, windowSeconds = 60), @RateLimit.Rule(key = RateLimit.LimitKey.IP, limit = 5, windowSeconds = 60)})
    @PostMapping("/forgot-password")
    public Result<Void> forgotPassword(@Valid @RequestBody ForgotPasswordDTO request) {
        authService.forgotPassword(request.getEmail());
        return Result.success(null);
    }

    @OperationLog(action = OperationLogConstants.ACTION_RESET_PASSWORD, module = OperationLogConstants.MODULE_AUTH)
    @PostMapping("/reset-password")
    public Result<Void> resetPassword(@Valid @RequestBody ResetPasswordDTO request, HttpServletResponse response) {
        authService.resetPassword(request);
        refreshCookieService.clear(response);
        return Result.success(null);
    }

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

    private Result<LoginVO> issue(IssuedAuthSession issued, HttpServletResponse response) {
        refreshCookieService.add(response, issued.refreshToken(), issued.refreshMaxAgeSeconds());
        return Result.success(issued.body());
    }
}