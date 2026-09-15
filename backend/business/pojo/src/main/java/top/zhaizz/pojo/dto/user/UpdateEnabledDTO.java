package top.zhaizz.pojo.dto.user;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/** UpdateEnabledDTO 数据对象 */
@Data
public class UpdateEnabledDTO {
    /** 用户或资源是否处于启用状态 */
    @NotNull(message = "启用状态不能为空")
    private Boolean enabled;
}
