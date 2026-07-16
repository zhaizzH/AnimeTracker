package top.zhaizz.user.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.user.service.AuthService;
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
    public Result<LoginVO> verifyEmail(@Valid @RequestBody VerifyEmailRequest request) {
        LoginVO loginVO = authService.verifyEmail(request.getEmail(), request.getCode());
        return Result.success(loginVO);
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
     * 用户注销
     */
    @GetMapping("/logout")
    public Result<Void> logout(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            authService.logout(token);
        }
        return Result.success(null);
    }

    /**
     * 验证邮箱请求体
     */
    @Data
    public static class VerifyEmailRequest {
        @NotBlank(message = "邮箱不能为空")
        @Email(message = "邮箱格式不正确")
        private String email;

        @NotBlank(message = "验证码不能为空")
        @Size(min = 6, max = 6, message = "验证码为6位")
        private String code;
    }
}
