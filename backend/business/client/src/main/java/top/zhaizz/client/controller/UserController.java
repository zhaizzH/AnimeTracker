package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.ClientUserService;
import top.zhaizz.client.service.RefreshCookieService;
import top.zhaizz.client.service.VerificationService;
import top.zhaizz.log.constant.OperationLogConstants;
import top.zhaizz.log.annotation.OperationLog;
import top.zhaizz.common.result.Result;
import top.zhaizz.auth.util.SecurityUtil;
import top.zhaizz.pojo.dto.auth.ChangeEmailSendCodeDTO;
import top.zhaizz.pojo.dto.auth.ChangeEmailVerifyDTO;
import top.zhaizz.pojo.dto.auth.ChangePasswordDTO;
import top.zhaizz.pojo.dto.user.UpdateUserDTO;
import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 个人信息控制器。
 */
@RestController
@RequestMapping("/api/client/me")
@RequiredArgsConstructor
public class UserController {

    /** 用户端用户服务。 */
    private final ClientUserService clientUserService;
    /** 验证码与邮箱验证服务。 */
    private final VerificationService verificationService;
    /** refresh Cookie 写入与清理服务。 */
    private final RefreshCookieService refreshCookieService;

    /**
     * 获取当前登录用户信息。
     * @return 统一成功响应，其数据为：当前登录用户信息
     */
    @GetMapping
    public Result<UserVO> getMyProfile() {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(clientUserService.getUserById(userId));
    }

    /**
     * 修改当前登录用户信息。
     * @param request 待更新的昵称和头像
     * @return 统一成功响应，其数据为：修改当前登录用户信息
     */
    @PostMapping("/update")
    public Result<UserVO> updateMyProfile(@Valid @RequestBody UpdateUserDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(clientUserService.updateUser(userId, request));
    }

    /**
     * 修改当前登录用户密码。
     * @param request 旧密码和新密码
     * @param response 用于写入 Cookie 的 HTTP 响应
     * @return 无数据的统一成功响应
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
     * 发送邮箱修改验证码（修改绑定邮箱前调用，校验新邮箱未被占用）。
     * @param request 待绑定的新邮箱及本次操作所需校验信息
     * @return 无数据的统一成功响应
     */
    @PostMapping("/send-email-code")
    public Result<Void> sendEmailCode(@Valid @RequestBody ChangeEmailSendCodeDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        verificationService.sendEmailChangeCode(userId, request.getNewEmail());
        return Result.success(null);
    }

    /**
     * 校验邮箱修改验证码（通过后更新绑定邮箱并通知旧邮箱）。
     * @param request 待绑定的新邮箱及本次操作所需校验信息
     * @return 无数据的统一成功响应
     */
    @PostMapping("/verify-email-code")
    public Result<Void> verifyEmailCode(@Valid @RequestBody ChangeEmailVerifyDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        verificationService.verifyEmailChangeCode(userId, request.getNewEmail(), request.getCode());
        return Result.success(null);
    }
}
