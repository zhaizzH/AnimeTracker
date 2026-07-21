package top.zhaizz.client.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.AuthService;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RefreshTokenDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.pojo.dto.ResendCodeDTO;
import top.zhaizz.pojo.dto.VerifyEmailDTO;
import top.zhaizz.pojo.vo.LoginVO;

/**
 * 认证控制器
 */
@RestController
@RequestMapping("/api/user/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * 用户注册
     * <p>创建用户并发送验证码邮件，注册成功后需调用 verify-email 完成验证</p>
     */
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterDTO request) {
        authService.register(request);
        return Result.success(null);
    }

    /**
     * 验证邮箱
     * <p>校验验证码，通过后标记邮箱已验证并返回 JWT Token 和用户信息</p>
     */
    @PostMapping("/verify-email")
    public Result<LoginVO> verifyEmail(@Valid @RequestBody VerifyEmailDTO request) {
        LoginVO loginVO = authService.verifyEmail(request.getEmail(), request.getCode());
        return Result.success(loginVO);
    }

    /**
     * 重新发送验证码
     */
    @PostMapping("/resend-code")
    public Result<Void> resendCode(@Valid @RequestBody ResendCodeDTO request) {
        authService.resendCode(request.getEmail());
        return Result.success(null);
    }

    /**
     * 用户登录
     */
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginDTO request) {
        LoginVO loginVO = authService.login(request);
        return Result.success(loginVO);
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
     * 用户注销
     */
    @PostMapping("/logout")
    public Result<Void> logout(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            authService.logout(token);
        }
        return Result.success(null);
    }
}
