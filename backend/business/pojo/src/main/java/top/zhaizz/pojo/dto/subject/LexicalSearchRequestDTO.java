package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.util.List;

/**
 * 受控 MySQL FULLTEXT 召回请求
 * <p>
 * subjectIds 是 Agent 经过实体关系解析后的 allowlist；它只用于缩小候选范围，
 * 不允许调用方把 SQL/MATCH 表达式直接传入
 */
public class LexicalSearchRequestDTO {
    /**
     * 词法检索关键词
     */
    @NotBlank(message = "搜索词不能为空")
    @Size(max = 100, message = "搜索词不能超过100字符")
    private String q;
    /**
     * 标签筛选列表，最多 20 项；每项非空且最多 64 个字符
     */
    @Size(max = 20, message = "标签最多20个")
    private List<@NotBlank(message = "标签不能为空") @Size(max = 64, message = "标签不能超过64字符") String> tags;
    /**
     * 评分筛选下限
     */
    @DecimalMin(value = "0", message = "最低评分不能小于0")
    @DecimalMax(value = "10", message = "最低评分不能大于10")
    private BigDecimal scoreMin;
    /**
     * 评分筛选上限
     */
    @DecimalMin(value = "0", message = "最高评分不能小于0")
    @DecimalMax(value = "10", message = "最高评分不能大于10")
    private BigDecimal scoreMax;
    /**
     * 年份筛选值
     */
    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private Integer year;
    /**
     * 星期筛选值
     */
    @Min(value = 0, message = "星期范围 0-6")
    @Max(value = 6, message = "星期范围 0-6")
    private Integer weekday;
    /**
     * 候选条目白名单，最多 50 个正整数 ID，用于缩小召回范围
     */
    @Size(max = 50, message = "条目 allowlist 最多50个")
    private List<@NotNull(message = "条目 ID 不能为空") @Positive(message = "条目 ID 必须为正数") Long> subjectIds;
    /**
     * 最多返回的候选数量
     */
    @Min(value = 1, message = "召回条数不能小于1")
    @Max(value = 50, message = "召回条数不能超过50")
    private int limit = 50;

    /** 创建召回条数默认为 50 的空请求对象 */
    public LexicalSearchRequestDTO() {
    }

    /**
     * 获取词法检索关键词
     * @return 用于 FULLTEXT 匹配的关键词；未提供时为 {@code null}，必填且不超过 100 字符
     */
    public String getQ() {
        return this.q;
    }

    /**
     * 获取标签筛选列表
     * @return 标签筛选列表；为 {@code null} 时不过滤标签，非空时最多 20 项、每项非空且不超过 64 字符
     */
    public List<@NotBlank(message = "标签不能为空") @Size(max = 64, message = "标签不能超过64字符") String> getTags() {
        return this.tags;
    }

    /**
     * 获取评分筛选下限
     * @return 评分筛选下限，取值 0~10；为 {@code null} 时不限制评分下界
     */
    public BigDecimal getScoreMin() {
        return this.scoreMin;
    }

    /**
     * 获取评分筛选上限
     * @return 评分筛选上限，取值 0~10；为 {@code null} 时不限制评分上界
     */
    public BigDecimal getScoreMax() {
        return this.scoreMax;
    }

    /**
     * 获取年份筛选值
     * @return 年份筛选值，取值 1970~2100；为 {@code null} 时不过滤年份
     */
    public Integer getYear() {
        return this.year;
    }

    /**
     * 获取星期筛选值
     * @return 星期筛选值，取值 0~6；为 {@code null} 时不过滤星期
     */
    public Integer getWeekday() {
        return this.weekday;
    }

    /**
     * 获取候选条目白名单
     * @return 用于缩小召回范围的条目 ID 白名单；为 {@code null} 时不限制候选，非空时最多 50 个正整数
     */
    public List<@NotNull(message = "条目 ID 不能为空") @Positive(message = "条目 ID 必须为正数") Long> getSubjectIds() {
        return this.subjectIds;
    }

    /**
     * 获取召回条数上限
     * @return 最多返回的候选数量，默认 50，取值需在 1~50 之间
     */
    public int getLimit() {
        return this.limit;
    }

    /**
     * 替换词法检索关键词
     * @param q 用于 FULLTEXT 匹配的关键词；可为 {@code null}，但校验要求其非空且不超过 100 字符
     */
    public void setQ(final String q) {
        this.q = q;
    }

    /**
     * 替换标签筛选列表
     * @param tags 标签筛选列表；可为 {@code null} 表示不过滤标签，非空时最多 20 项、每项非空且不超过 64 字符
     */
    public void setTags(final List<@NotBlank(message = "标签不能为空") @Size(max = 64, message = "标签不能超过64字符") String> tags) {
        this.tags = tags;
    }

    /**
     * 替换评分筛选下限
     * @param scoreMin 评分筛选下限，取值 0~10；可为 {@code null} 表示不限制评分下界
     */
    public void setScoreMin(final BigDecimal scoreMin) {
        this.scoreMin = scoreMin;
    }

    /**
     * 替换评分筛选上限
     * @param scoreMax 评分筛选上限，取值 0~10；可为 {@code null} 表示不限制评分上界
     */
    public void setScoreMax(final BigDecimal scoreMax) {
        this.scoreMax = scoreMax;
    }

    /**
     * 替换年份筛选值
     * @param year 年份筛选值，取值 1970~2100；可为 {@code null} 表示不过滤年份
     */
    public void setYear(final Integer year) {
        this.year = year;
    }

    /**
     * 替换星期筛选值
     * @param weekday 星期筛选值，取值 0~6；可为 {@code null} 表示不过滤星期
     */
    public void setWeekday(final Integer weekday) {
        this.weekday = weekday;
    }

    /**
     * 替换候选条目白名单
     * @param subjectIds 用于缩小召回范围的条目 ID 白名单；可为 {@code null}，非空时最多 50 个正整数
     */
    public void setSubjectIds(final List<@NotNull(message = "条目 ID 不能为空") @Positive(message = "条目 ID 必须为正数") Long> subjectIds) {
        this.subjectIds = subjectIds;
    }

    /**
     * 替换召回条数上限
     * @param limit 最多返回的候选数量，需在 1~50 之间
     */
    public void setLimit(final int limit) {
        this.limit = limit;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LexicalSearchRequestDTO)) return false;
        final LexicalSearchRequestDTO other = (LexicalSearchRequestDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getLimit() != other.getLimit()) return false;
        final Object thisYear = this.getYear();
        final Object otherYear = other.getYear();
        if (thisYear == null ? otherYear != null : !thisYear.equals(otherYear)) return false;
        final Object thisWeekday = this.getWeekday();
        final Object otherWeekday = other.getWeekday();
        if (thisWeekday == null ? otherWeekday != null : !thisWeekday.equals(otherWeekday)) return false;
        final Object thisQ = this.getQ();
        final Object otherQ = other.getQ();
        if (thisQ == null ? otherQ != null : !thisQ.equals(otherQ)) return false;
        final Object thisTags = this.getTags();
        final Object otherTags = other.getTags();
        if (thisTags == null ? otherTags != null : !thisTags.equals(otherTags)) return false;
        final Object thisScoreMin = this.getScoreMin();
        final Object otherScoreMin = other.getScoreMin();
        if (thisScoreMin == null ? otherScoreMin != null : !thisScoreMin.equals(otherScoreMin)) return false;
        final Object thisScoreMax = this.getScoreMax();
        final Object otherScoreMax = other.getScoreMax();
        if (thisScoreMax == null ? otherScoreMax != null : !thisScoreMax.equals(otherScoreMax)) return false;
        final Object thisSubjectIds = this.getSubjectIds();
        final Object otherSubjectIds = other.getSubjectIds();
        if (thisSubjectIds == null ? otherSubjectIds != null : !thisSubjectIds.equals(otherSubjectIds)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof LexicalSearchRequestDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + this.getLimit();
        final Object hashYear = this.getYear();
        result = result * PRIME + (hashYear == null ? 43 : hashYear.hashCode());
        final Object hashWeekday = this.getWeekday();
        result = result * PRIME + (hashWeekday == null ? 43 : hashWeekday.hashCode());
        final Object hashQ = this.getQ();
        result = result * PRIME + (hashQ == null ? 43 : hashQ.hashCode());
        final Object hashTags = this.getTags();
        result = result * PRIME + (hashTags == null ? 43 : hashTags.hashCode());
        final Object hashScoreMin = this.getScoreMin();
        result = result * PRIME + (hashScoreMin == null ? 43 : hashScoreMin.hashCode());
        final Object hashScoreMax = this.getScoreMax();
        result = result * PRIME + (hashScoreMax == null ? 43 : hashScoreMax.hashCode());
        final Object hashSubjectIds = this.getSubjectIds();
        result = result * PRIME + (hashSubjectIds == null ? 43 : hashSubjectIds.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "LexicalSearchRequestDTO(q=" + this.getQ() + ", tags=" + this.getTags() + ", scoreMin=" + this.getScoreMin() + ", scoreMax=" + this.getScoreMax() + ", year=" + this.getYear() + ", weekday=" + this.getWeekday() + ", subjectIds=" + this.getSubjectIds() + ", limit=" + this.getLimit() + ")";
    }
}
