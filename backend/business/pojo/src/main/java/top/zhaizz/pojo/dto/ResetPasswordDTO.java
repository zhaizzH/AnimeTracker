package top.zhaizz.pojo.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 忘记密码 — 重置密码请求 DTO
 */
@Data
public class ResetPasswordDTO {

    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;       // 邮箱

    @NotBlank(message = "验证码不能为空")
    @Size(min = 6, max = 6, message = "验证码为6位")
    private String code;        // 验证码（6位）

    @NotBlank(message = "新密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度需在6~128之间")
    private String newPassword; // 新密码
}
