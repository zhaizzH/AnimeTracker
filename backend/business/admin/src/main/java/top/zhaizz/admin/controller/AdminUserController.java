package top.zhaizz.admin.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.admin.service.AdminUserService;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.user.UpdateRoleDTO;
import top.zhaizz.pojo.dto.user.UpdateEnabledDTO;
import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 用户管理控制器
 */
@RestController
@RequestMapping("/api/admin/users")
@RequiredArgsConstructor
@Validated
public class AdminUserController {

    private final AdminUserService adminUserService;

    /**
     * 分页查看所有注册用户（不返回密码字段），管理后台用户列表加载时触发
     */
    @GetMapping
    public Result<PageResult<UserVO>> listUsers(
            @RequestParam(defaultValue = "1") @Min(value = 1, message = "页码不能小于1") int page,
            @RequestParam(defaultValue = "20") @Min(value = 1, message = "每页条数不能小于1") @Max(value = 100, message = "每页条数不能超过100") int size) {
        return Result.success(adminUserService.listUsers(page, size));
    }

    /**
     * 修改指定用户的角色，管理后台角色变更提交时触发
     */
    @OperationLog(action = OperationLogConstants.ACTION_ROLE_CHANGE, module = OperationLogConstants.MODULE_ADMIN)
    @PostMapping("/{id}/update-role")
    public Result<UserVO> updateUserRole(
            @PathVariable Long id,
            @Valid @RequestBody UpdateRoleDTO request) {
        return Result.success(adminUserService.updateUserRole(id, request.getRole()));
    }
    @PostMapping("/{id}/update-enabled")
    public Result<UserVO> updateUserEnabled(@PathVariable Long id, @Valid @RequestBody UpdateEnabledDTO request) {
        return Result.success(adminUserService.updateUserEnabled(id, request.getEnabled()));
    }
}
