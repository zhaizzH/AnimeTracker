package top.zhaizz.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * 登录/注册结果 VO（token + 用户信息）
 * <p>
 * 注册和登录统一返回此结构，前端一次拿到 Token 和用户信息，
 * 无需额外调用 {@code GET /api/client/me}。
 */
@Data
@AllArgsConstructor
public class LoginVO {

    private String token;           // Access Token
    private String refreshToken;    // Refresh Token（轮换）
    private UserVO user;            // 用户信息
}
