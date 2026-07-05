package top.zhaizz.animetracker.user.service;

import top.zhaizz.animetracker.common.dto.LoginDTO;
import top.zhaizz.animetracker.common.dto.RegisterDTO;
import top.zhaizz.animetracker.common.vo.LoginVO;
import top.zhaizz.animetracker.common.vo.UserVO;

/**
 * 认证服务接口
 */
public interface AuthService {

    /**
     * 用户注册
     */
    UserVO register(RegisterDTO request);

    /**
     * 用户登录
     *
     * @return LoginResult（含 JWT Token 和用户信息）
     */
    LoginVO login(LoginDTO request);

    /**
     * 生成 JWT Token
     */
    String generateToken(Long userId, String role);
}
