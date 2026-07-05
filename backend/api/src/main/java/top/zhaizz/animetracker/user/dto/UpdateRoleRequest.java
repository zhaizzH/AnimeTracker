package top.zhaizz.animetracker.user.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/**
 * 修改角色请求 DTO
 */
@Data
public class UpdateRoleRequest {

    @NotBlank(message = "角色不能为空")
    @Pattern(regexp = "USER|ADMIN", message = "角色值必须是 USER 或 ADMIN")
    private String role;
}
