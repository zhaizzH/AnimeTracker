package top.zhaizz.user.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.UpdateRoleDTO;
import top.zhaizz.user.service.UserService;
import top.zhaizz.pojo.vo.UserVO;

/**
 * 管理员用户管理控制器
 */
@RestController
@RequestMapping("/api/admin/users")
@RequiredArgsConstructor
public class AdminUserController {

    private final UserService userService;

    /**
     * 分页查看所有注册用户（不返回密码字段）
     */
    @GetMapping
    public Result<PageResult<UserVO>> listUsers(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        return Result.success(userService.listUsers(page, size));
    }

    /**
     * 修改指定用户的角色
     * <p>
     * `@Valid` 定义校验规则,在 UpdateRoleRequest 类中使用 @NotBlank、@NotNull、@Size 等注解定义校验规则
     */
    @PutMapping("/{id}/role")
    public Result<UserVO> updateUserRole(
            @PathVariable Long id,
            @Valid @RequestBody UpdateRoleDTO request) {
        return Result.success(userService.updateUserRole(id, request.getRole()));
    }
}
