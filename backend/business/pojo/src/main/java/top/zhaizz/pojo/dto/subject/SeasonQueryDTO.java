package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/** 季度查询参数 */
@Data
public class SeasonQueryDTO {

    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private int year;           // 年份（primitive，缺参绑 0 由 @Min 兜底）

    @NotBlank(message = "季度不能为空")
    @Pattern(regexp = "spring|summer|autumn|winter", message = "季度仅允许: spring/summer/autumn/winter")
    private String quarter;     // 季度: spring/summer/autumn/winter

    @Min(value = 1, message = "页码不能小于1")
    private int page = 1;       // 页码

    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20;      // 每页条数
}
