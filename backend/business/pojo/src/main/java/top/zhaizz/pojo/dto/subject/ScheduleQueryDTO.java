package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/** 每周追番查询参数（weekday=-1 为哨兵：不过滤星期） */
@Data
public class ScheduleQueryDTO {
    @Min(value = -1, message = "星期范围 -1 到 6")
    @Max(value = 6, message = "星期范围 -1 到 6")
    private int weekday = -1;       // 播出星期（-1=不限, 0=周日 ... 6=周六）

    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private Integer year;           // 年份（空=当前季度年份）

    @Pattern(regexp = "spring|summer|autumn|winter", message = "季度仅允许: spring/summer/autumn/winter")
    private String quarter;         // 季度（空=当前季度）

    @Min(value = 1, message = "页码不能小于1")
    private int page = 1;           // 页码

    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20;          // 每页条数（原默认 50，刻意改为 20）
}
