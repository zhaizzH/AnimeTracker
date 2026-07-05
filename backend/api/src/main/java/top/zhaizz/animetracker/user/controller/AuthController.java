package top.zhaizz.animetracker.user.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.ApiResponse;
import top.zhaizz.animetracker.user.dto.LoginRequest;
import top.zhaizz.animetracker.user.dto.RegisterRequest;
import top.zhaizz.animetracker.user.service.AuthService;
import top.zhaizz.animetracker.user.vo.LoginResult;
import top.zhaizz.animetracker.user.vo.UserVO;

/**
 * 认证控制器：注册 / 登录
 */
@RestController
@RequestMapping("/api/user/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * 用户注册
     * <p>注册成功后自动登录，返回 JWT Token 和用户信息</p>
     */
    @PostMapping("/register")
    public ApiResponse<LoginResult> register(@Valid @RequestBody RegisterRequest request) {
        UserVO userVO = authService.register(request);
        // 注册成功后自动登录，返回 Token + 用户信息
        LoginResult loginResult = authService.login(
                new LoginRequest(request.getUsername(), request.getPassword()));
        return ApiResponse.success(loginResult);
    }

    /**
     * 用户登录
     * <p>登录成功返回 JWT Token 和用户信息</p>
     */
    @PostMapping("/login")
    public ApiResponse<LoginResult> login(@Valid @RequestBody LoginRequest request) {
        LoginResult loginResult = authService.login(request);
        return ApiResponse.success(loginResult);
    }
}
