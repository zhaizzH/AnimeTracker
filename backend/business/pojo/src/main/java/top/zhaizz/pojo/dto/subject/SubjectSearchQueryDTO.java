package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

/** 番剧搜索查询参数 */
@Data
public class SubjectSearchQueryDTO {
    @Size(max = 100, message = "搜索词不能超过100字符")
    private String q;               // 搜索词（service 内 trim）

    @Size(max = 20, message = "标签最多20个")
    private List<String> tag;       // 标签筛选

    @DecimalMin(value = "0", message = "最低评分不能小于0")
    @DecimalMax(value = "10", message = "最低评分不能大于10")
    private BigDecimal scoreMin;    // 最低评分

    @DecimalMin(value = "0", message = "最高评分不能小于0")
    @DecimalMax(value = "10", message = "最高评分不能大于10")
    private BigDecimal scoreMax;    // 最高评分

    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private Integer year;           // 年份

    @Min(value = 0, message = "星期范围 0-6")
    @Max(value = 6, message = "星期范围 0-6")
    private Integer weekday;        // 播出星期

    private String sort = "score";  // 排序字段（进 SQL 走白名单）

    private String order = "desc";  // 排序方向（asc/desc）

    @Min(value = 1, message = "页码不能小于1")
    private int page = 1;           // 页码

    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20;          // 每页条数
}
