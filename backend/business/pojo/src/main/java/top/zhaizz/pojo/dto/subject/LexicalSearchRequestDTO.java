package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

/**
 * 受控 MySQL FULLTEXT 召回请求。
 * <p>
 * subjectIds 是 Agent 经过实体关系解析后的 allowlist；它只用于缩小候选范围，
 * 不允许调用方把 SQL/MATCH 表达式直接传入。
 */
@Data
public class LexicalSearchRequestDTO {

    @NotBlank(message = "搜索词不能为空")
    @Size(max = 100, message = "搜索词不能超过100字符")
    private String q;

    @Size(max = 20, message = "标签最多20个")
    private List<@NotBlank(message = "标签不能为空") @Size(max = 64, message = "标签不能超过64字符") String> tags;

    @DecimalMin(value = "0", message = "最低评分不能小于0")
    @DecimalMax(value = "10", message = "最低评分不能大于10")
    private BigDecimal scoreMin;

    @DecimalMin(value = "0", message = "最高评分不能小于0")
    @DecimalMax(value = "10", message = "最高评分不能大于10")
    private BigDecimal scoreMax;

    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private Integer year;

    @Min(value = 0, message = "星期范围 0-6")
    @Max(value = 6, message = "星期范围 0-6")
    private Integer weekday;

    @Size(max = 50, message = "条目 allowlist 最多50个")
    private List<@NotNull(message = "条目 ID 不能为空") @Positive(message = "条目 ID 必须为正数") Long> subjectIds;

    @Min(value = 1, message = "召回条数不能小于1")
    @Max(value = 50, message = "召回条数不能超过50")
    private int limit = 50;
}
