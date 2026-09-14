package top.zhaizz.pojo.vo.auth;

import lombok.AllArgsConstructor;
import lombok.Data;
import top.zhaizz.pojo.vo.user.UserVO;

/** 登录/验证结果（access token + 用户信息；refresh token 仅通过 HttpOnly Cookie 返回）。 */
@Data
@AllArgsConstructor
public class LoginVO {
    /** 认证或会话令牌。 */
    private String token;
    /** 认证成功后的用户信息。 */
    private UserVO user;
}
