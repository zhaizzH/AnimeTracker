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

    /** 词法检索关键词。 */
    @NotBlank(message = "搜索词不能为空")
    @Size(max = 100, message = "搜索词不能超过100字符")
    private String q;

    /**
     * 标签筛选列表，最多 20 项；每项非空且最多 64 个字符。
     */
    @Size(max = 20, message = "标签最多20个")
    private List<@NotBlank(message = "标签不能为空") @Size(max = 64, message = "标签不能超过64字符") String> tags;

    /** 评分筛选下限。 */
    @DecimalMin(value = "0", message = "最低评分不能小于0")
    @DecimalMax(value = "10", message = "最低评分不能大于10")
    private BigDecimal scoreMin;

    /** 评分筛选上限。 */
    @DecimalMin(value = "0", message = "最高评分不能小于0")
    @DecimalMax(value = "10", message = "最高评分不能大于10")
    private BigDecimal scoreMax;

    /** 年份筛选值。 */
    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private Integer year;

    /** 星期筛选值。 */
    @Min(value = 0, message = "星期范围 0-6")
    @Max(value = 6, message = "星期范围 0-6")
    private Integer weekday;

    /**
     * 候选条目白名单，最多 50 个正整数 ID，用于缩小召回范围。
     */
    @Size(max = 50, message = "条目 allowlist 最多50个")
    private List<@NotNull(message = "条目 ID 不能为空") @Positive(message = "条目 ID 必须为正数") Long> subjectIds;

    /** 最多返回的候选数量。 */
    @Min(value = 1, message = "召回条数不能小于1")
    @Max(value = 50, message = "召回条数不能超过50")
    private int limit = 50;
}
