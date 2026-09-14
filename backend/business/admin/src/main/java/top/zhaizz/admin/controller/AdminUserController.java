package top.zhaizz.admin.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.admin.service.AdminUserService;
import top.zhaizz.log.constant.OperationLogConstants;
import top.zhaizz.log.annotation.OperationLog;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.user.UpdateRoleDTO;
import top.zhaizz.pojo.dto.user.UpdateEnabledDTO;
import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 用户管理控制器。
 */
@RestController
@RequestMapping("/api/admin/users")
@RequiredArgsConstructor
@Validated
public class AdminUserController {

    /** 管理员用户管理服务。 */
    private final AdminUserService adminUserService;

    /**
     * 分页查看所有注册用户（不返回密码字段），管理后台用户列表加载时触发。
     * @param page 分页页码，从 1 开始
     * @param size 每页记录数
     * @return 统一成功响应，其数据为：按注册时间降序排列的用户分页
     */
    @GetMapping
    public Result<PageResult<UserVO>> listUsers(
            @RequestParam(defaultValue = "1") @Min(value = 1, message = "页码不能小于1") int page,
            @RequestParam(defaultValue = "20") @Min(value = 1, message = "每页条数不能小于1") @Max(value = 100, message = "每页条数不能超过100") int size) {
        return Result.success(adminUserService.listUsers(page, size));
    }

    /**
     * 修改指定用户的角色，管理后台角色变更提交时触发。
     * @param id 目标条目 ID
     * @param request 目标用户角色
     * @return 统一成功响应，其数据为：修改角色后的用户信息
     */
    @OperationLog(action = OperationLogConstants.ACTION_ROLE_CHANGE, module = OperationLogConstants.MODULE_ADMIN)
    @PostMapping("/{id}/update-role")
    public Result<UserVO> updateUserRole(
            @PathVariable Long id,
            @Valid @RequestBody UpdateRoleDTO request) {
        return Result.success(adminUserService.updateUserRole(id, request.getRole()));
    }
    /**
     * 修改目标账户的启用状态。
     * @param id 目标条目 ID
     * @param request 目标账户启用状态
     * @return 统一成功响应，其数据为：修改启用状态后的用户信息
     */
    @PostMapping("/{id}/update-enabled")
    public Result<UserVO> updateUserEnabled(@PathVariable Long id, @Valid @RequestBody UpdateEnabledDTO request) {
        return Result.success(adminUserService.updateUserEnabled(id, request.getEnabled()));
    }
}
