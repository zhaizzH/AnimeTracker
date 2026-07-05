package top.zhaizz.animetracker.user.service;

import top.zhaizz.animetracker.user.dto.LoginRequest;
import top.zhaizz.animetracker.user.dto.RegisterRequest;
import top.zhaizz.animetracker.user.vo.LoginResult;
import top.zhaizz.animetracker.user.vo.UserVO;

/**
 * 认证服务接口
 */
public interface AuthService {

    /**
     * 用户注册
     */
    UserVO register(RegisterRequest request);

    /**
     * 用户登录
     *
     * @return LoginResult（含 JWT Token 和用户信息）
     */
    LoginResult login(LoginRequest request);

    /**
     * 生成 JWT Token
     */
    String generateToken(Long userId, String role);
}
