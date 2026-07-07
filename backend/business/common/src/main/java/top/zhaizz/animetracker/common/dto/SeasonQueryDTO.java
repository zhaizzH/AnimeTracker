package top.zhaizz.animetracker.common.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/**
 * 季度查询参数
 */
@Data
public class SeasonQueryDTO {

    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private int year;

    @Pattern(regexp = "spring|summer|autumn|winter", message = "季度仅允许: spring/summer/autumn/winter")
    private String quarter;
}
