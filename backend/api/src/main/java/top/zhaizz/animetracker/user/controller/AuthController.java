package top.zhaizz.animetracker.user.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.ApiResponse;
import top.zhaizz.animetracker.common.dto.LoginDTO;
import top.zhaizz.animetracker.common.dto.RegisterDTO;
import top.zhaizz.animetracker.user.service.AuthService;
import top.zhaizz.animetracker.common.vo.LoginVO;
import top.zhaizz.animetracker.common.vo.UserVO;

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
    public ApiResponse<LoginVO> register(@Valid @RequestBody RegisterDTO request) {
        UserVO userVO = authService.register(request);
        // 注册成功后自动登录，返回 Token + 用户信息
        LoginVO loginVO = authService.login(
                new LoginDTO(request.getUsername(), request.getPassword()));
        return ApiResponse.success(loginVO);
    }

    /**
     * 用户登录
     * <p>登录成功返回 JWT Token 和用户信息</p>
     */
    @PostMapping("/login")
    public ApiResponse<LoginVO> login(@Valid @RequestBody LoginDTO request) {
        LoginVO loginVO = authService.login(request);
        return ApiResponse.success(loginVO);
    }
}
