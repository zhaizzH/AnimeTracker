package top.zhaizz.user.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.user.service.AuthService;
import top.zhaizz.pojo.vo.LoginVO;
import top.zhaizz.pojo.vo.UserVO;

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
     * <p>注册成功后自动登录，返回 JWT Token 和用户信息</p>
     */
    @PostMapping("/register")
    public Result<LoginVO> register(@Valid @RequestBody RegisterDTO request) {
        UserVO userVO = authService.register(request);
        // 注册成功后自动登录，返回 Token + 用户信息
        LoginVO loginVO = authService.login(
                new LoginDTO(request.getUsername(), request.getPassword()));
        return Result.success(loginVO);
    }

    /**
     * 用户登录
     * <p>登录成功返回 JWT Token 和用户信息</p>
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
}
