package top.zhaizz.pojo.dto.user;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class UpdateEnabledDTO {
    @NotNull(message = "启用状态不能为空")
    private Boolean enabled;
}