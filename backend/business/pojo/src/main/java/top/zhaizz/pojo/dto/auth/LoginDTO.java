package top.zhaizz.pojo.dto.auth;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 登录请求 DTO。
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginDTO {

    /** 用户名或邮箱。 */
    @NotBlank(message = "用户名或邮箱不能为空")
    private String username;    // 用户名或邮箱
    /** 密码。 */
    @NotBlank(message = "密码不能为空")
    private String password;    // 密码
}
