package top.zhaizz.animetracker.common.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 修改个人信息请求 DTO
 */
@Data
public class UpdateUserDTO {

    @Size(max = 64, message = "昵称长度不能超过64")
    private String nickname;

    @Size(max = 512, message = "头像URL长度不能超过512")
    private String avatar;

    @Email(message = "邮箱格式不正确")
    @Size(max = 128, message = "邮箱长度不能超过128")
    private String email;
}
