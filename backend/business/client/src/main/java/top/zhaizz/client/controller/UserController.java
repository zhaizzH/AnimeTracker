package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.ClientUserService;
import top.zhaizz.client.service.RefreshCookieService;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.util.SecurityUtil;
import top.zhaizz.pojo.dto.auth.ChangeEmailSendCodeDTO;
import top.zhaizz.pojo.dto.auth.ChangeEmailVerifyDTO;
import top.zhaizz.pojo.dto.auth.ChangePasswordDTO;
import top.zhaizz.pojo.dto.user.UpdateUserDTO;
import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 个人信息控制器
 */
@RestController
@RequestMapping("/api/client/me")
@RequiredArgsConstructor
public class UserController {

    private final ClientUserService clientUserService;
    private final VerificationService verificationService;
    private final RefreshCookieService refreshCookieService;

    /**
     * 获取当前登录用户信息
     */
    @GetMapping
    public Result<UserVO> getMyProfile() {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(clientUserService.getUserById(userId));
    }

    /**
     * 修改当前登录用户信息
     */
    @PostMapping("/update")
    public Result<UserVO> updateMyProfile(@Valid @RequestBody UpdateUserDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(clientUserService.updateUser(userId, request));
    }

    /**
     * 修改当前登录用户密码
     */
    @OperationLog(action = OperationLogConstants.ACTION_PASSWORD_CHANGE, module = OperationLogConstants.MODULE_USER)
    @PostMapping("/update-password")
    public Result<Void> changePassword(@Valid @RequestBody ChangePasswordDTO request, HttpServletResponse response) {
        Long userId = SecurityUtil.getCurrentUserId();
        clientUserService.changePassword(userId, request);
        refreshCookieService.clear(response);
        return Result.success(null);
    }

    /**
     * 发送邮箱修改验证码（修改绑定邮箱前调用，校验新邮箱未被占用）
     */
    @PostMapping("/send-email-code")
    public Result<Void> sendEmailCode(@Valid @RequestBody ChangeEmailSendCodeDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        verificationService.sendEmailChangeCode(userId, request.getNewEmail());
        return Result.success(null);
    }

    /**
     * 校验邮箱修改验证码（通过后更新绑定邮箱并通知旧邮箱）
     */
    @PostMapping("/verify-email-code")
    public Result<Void> verifyEmailCode(@Valid @RequestBody ChangeEmailVerifyDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        verificationService.verifyEmailChangeCode(userId, request.getNewEmail(), request.getCode());
        return Result.success(null);
    }
}
