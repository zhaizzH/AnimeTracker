package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.ClientUserService;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.vo.UserVO;

/**
 * 个人信息控制器
 */
@RestController
@RequestMapping("/api/user/me")
@RequiredArgsConstructor
public class UserController {

    private final ClientUserService clientUserService;
    private final VerificationService verificationService;

    /**
     * 获取当前登录用户信息
     */
    @GetMapping
    public Result<UserVO> getMyProfile() {
        Long userId = getCurrentUserId();
        return Result.success(clientUserService.getUserById(userId));
    }

    /**
     * 修改当前登录用户信息
     */
    @PutMapping
    public Result<UserVO> updateMyProfile(@Valid @RequestBody UpdateUserDTO request) {
        Long userId = getCurrentUserId();
        return Result.success(clientUserService.updateUser(userId, request));
    }

    /**
     * 发送邮箱修改验证码
     */
    @PostMapping("/send-email-code")
    public Result<Void> sendEmailCode(@Valid @RequestBody SendEmailCodeRequest request) {
        Long userId = getCurrentUserId();
        verificationService.sendEmailChangeCode(userId, request.getNewEmail());
        return Result.success(null);
    }

    /**
     * 校验邮箱修改验证码 -> 更新邮箱
     */
    @PostMapping("/verify-email-code")
    public Result<Void> verifyEmailCode(@Valid @RequestBody VerifyEmailCodeRequest request) {
        Long userId = getCurrentUserId();
        verificationService.verifyEmailChangeCode(userId, request.getNewEmail(), request.getCode());
        return Result.success(null);
    }

    /**
     * 从 SecurityContext 获取当前用户 ID
     * <p>
     * JwtAuthenticationFilter 在认证时将 userId 设置到 Authentication.principal 中。
     */
    private Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return (Long) auth.getPrincipal();
    }

    @Data
    public static class SendEmailCodeRequest {
        @NotBlank(message = "新邮箱不能为空")
        @Email(message = "邮箱格式不正确")
        @Size(max = 128, message = "邮箱长度不能超过128")
        private String newEmail;
    }

    @Data
    public static class VerifyEmailCodeRequest {
        @NotBlank(message = "新邮箱不能为空")
        @Email(message = "邮箱格式不正确")
        @Size(max = 128, message = "邮箱长度不能超过128")
        private String newEmail;

        @NotBlank(message = "验证码不能为空")
        @Size(min = 6, max = 6, message = "验证码为6位")
        private String code;
    }
}
