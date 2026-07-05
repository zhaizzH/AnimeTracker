package top.zhaizz.animetracker.user.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.ApiResponse;
import top.zhaizz.animetracker.user.dto.UpdateUserRequest;
import top.zhaizz.animetracker.user.service.UserService;
import top.zhaizz.animetracker.user.vo.UserVO;

/**
 * 个人信息控制器：查看 / 修改个人信息
 */
@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /**
     * 获取当前登录用户信息
     */
    @GetMapping("/me")
    public ApiResponse<UserVO> getMyProfile() {
        Long userId = getCurrentUserId();
        return ApiResponse.success(userService.getUserById(userId));
    }

    /**
     * 修改当前登录用户信息
     */
    @PutMapping("/me")
    public ApiResponse<UserVO> updateMyProfile(@Valid @RequestBody UpdateUserRequest request) {
        Long userId = getCurrentUserId();
        return ApiResponse.success(userService.updateUser(userId, request));
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
}
