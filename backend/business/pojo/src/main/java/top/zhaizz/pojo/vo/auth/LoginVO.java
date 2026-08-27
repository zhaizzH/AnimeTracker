package top.zhaizz.pojo.vo.auth;

import lombok.AllArgsConstructor;
import lombok.Data;
import top.zhaizz.pojo.vo.user.UserVO;

/** 登录/验证结果（access token + 用户信息；refresh token 仅通过 HttpOnly Cookie 返回） */
@Data
@AllArgsConstructor
public class LoginVO {
    private String token;
    private UserVO user;
}