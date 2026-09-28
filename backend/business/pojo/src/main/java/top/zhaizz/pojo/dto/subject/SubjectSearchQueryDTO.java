package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.util.List;

/**
 * 番剧搜索查询参数
 */
public class SubjectSearchQueryDTO {
    /**
     * 搜索词（service 内 trim）
     */
    @Size(max = 100, message = "搜索词不能超过100字符")
    private String q; // 搜索词（service 内 trim）
    /**
     * 标签筛选
     */
    @Size(max = 20, message = "标签最多20个")
    private List<String> tag; // 标签筛选
    /**
     * 最低评分
     */
    @DecimalMin(value = "0", message = "最低评分不能小于0")
    @DecimalMax(value = "10", message = "最低评分不能大于10")
    private BigDecimal scoreMin; // 最低评分
    /**
     * 最高评分
     */
    @DecimalMin(value = "0", message = "最高评分不能小于0")
    @DecimalMax(value = "10", message = "最高评分不能大于10")
    private BigDecimal scoreMax; // 最高评分
    /**
     * 年份
     */
    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private Integer year; // 年份
    /**
     * 播出星期
     */
    @Min(value = 0, message = "星期范围 0-6")
    @Max(value = 6, message = "星期范围 0-6")
    private Integer weekday; // 播出星期
    /**
     * 排序字段（进 SQL 走白名单）
     */
    private String sort = "score"; // 排序字段（进 SQL 走白名单）
    /**
     * 排序方向（asc/desc）
     */
    private String order = "desc"; // 排序方向（asc/desc）
    /**
     * 页码
     */
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1; // 页码
    /**
     * 每页条数
     */
    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20; // 每页条数

    /** 创建使用默认排序与分页参数的空查询对象 */
    public SubjectSearchQueryDTO() {
    }

    /**
     * 获取搜索词
     * @return 搜索关键词，服务层会先做 trim；为 {@code null} 时不按关键词过滤，非空时不超过 100 字符
     */
    public String getQ() {
        return this.q;
    }

    /**
     * 获取标签筛选列表
     * @return 标签筛选项；为 {@code null} 时不过滤标签，非空时最多 20 个
     */
    public List<String> getTag() {
        return this.tag;
    }

    /**
     * 获取最低评分
     * @return 评分筛选下限，取值 0~10；为 {@code null} 时不限制评分下界
     */
    public BigDecimal getScoreMin() {
        return this.scoreMin;
    }

    /**
     * 获取最高评分
     * @return 评分筛选上限，取值 0~10；为 {@code null} 时不限制评分上界
     */
    public BigDecimal getScoreMax() {
        return this.scoreMax;
    }

    /**
     * 获取年份
     * @return 年份筛选值，取值 1970~2100；为 {@code null} 时不过滤年份
     */
    public Integer getYear() {
        return this.year;
    }

    /**
     * 获取播出星期
     * @return 播出星期筛选值，取值 0~6；为 {@code null} 时不过滤星期
     */
    public Integer getWeekday() {
        return this.weekday;
    }

    /**
     * 获取排序字段
     * @return 排序字段名，默认 score；取值会经白名单校验后再拼入 SQL
     */
    public String getSort() {
        return this.sort;
    }

    /**
     * 获取排序方向
     * @return 排序方向 asc 或 desc，默认 desc
     */
    public String getOrder() {
        return this.order;
    }

    /**
     * 获取页码
     * @return 当前页码，默认 1，取值不得小于 1
     */
    public int getPage() {
        return this.page;
    }

    /**
     * 获取每页条数
     * @return 单页记录数，默认 20，取值需在 1~100 之间
     */
    public int getSize() {
        return this.size;
    }

    /**
     * 替换搜索词
     * @param q 搜索关键词，服务层会先做 trim；可为 {@code null} 表示不按关键词过滤，非空时不超过 100 字符
     */
    public void setQ(final String q) {
        this.q = q;
    }

    /**
     * 替换标签筛选列表
     * @param tag 标签筛选项；可为 {@code null} 表示不过滤标签，非空时最多 20 个
     */
    public void setTag(final List<String> tag) {
        this.tag = tag;
    }

    /**
     * 替换最低评分
     * @param scoreMin 评分筛选下限，取值 0~10；可为 {@code null} 表示不限制评分下界
     */
    public void setScoreMin(final BigDecimal scoreMin) {
        this.scoreMin = scoreMin;
    }

    /**
     * 替换最高评分
     * @param scoreMax 评分筛选上限，取值 0~10；可为 {@code null} 表示不限制评分上界
     */
    public void setScoreMax(final BigDecimal scoreMax) {
        this.scoreMax = scoreMax;
    }

    /**
     * 替换年份
     * @param year 年份筛选值，取值 1970~2100；可为 {@code null} 表示不过滤年份
     */
    public void setYear(final Integer year) {
        this.year = year;
    }

    /**
     * 替换播出星期
     * @param weekday 播出星期筛选值，取值 0~6；可为 {@code null} 表示不过滤星期
     */
    public void setWeekday(final Integer weekday) {
        this.weekday = weekday;
    }

    /**
     * 替换排序字段
     * @param sort 排序字段名，非白名单取值会被拒绝
     */
    public void setSort(final String sort) {
        this.sort = sort;
    }

    /**
     * 替换排序方向
     * @param order 排序方向 asc 或 desc
     */
    public void setOrder(final String order) {
        this.order = order;
    }

    /**
     * 替换页码
     * @param page 新的页码，从 1 开始，不得小于 1
     */
    public void setPage(final int page) {
        this.page = page;
    }

    /**
     * 替换每页条数
     * @param size 新的单页记录数，需在 1~100 之间
     */
    public void setSize(final int size) {
        this.size = size;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectSearchQueryDTO)) return false;
        final SubjectSearchQueryDTO other = (SubjectSearchQueryDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getPage() != other.getPage()) return false;
        if (this.getSize() != other.getSize()) return false;
        final Object thisYear = this.getYear();
        final Object otherYear = other.getYear();
        if (thisYear == null ? otherYear != null : !thisYear.equals(otherYear)) return false;
        final Object thisWeekday = this.getWeekday();
        final Object otherWeekday = other.getWeekday();
        if (thisWeekday == null ? otherWeekday != null : !thisWeekday.equals(otherWeekday)) return false;
        final Object thisQ = this.getQ();
        final Object otherQ = other.getQ();
        if (thisQ == null ? otherQ != null : !thisQ.equals(otherQ)) return false;
        final Object thisTag = this.getTag();
        final Object otherTag = other.getTag();
        if (thisTag == null ? otherTag != null : !thisTag.equals(otherTag)) return false;
        final Object thisScoreMin = this.getScoreMin();
        final Object otherScoreMin = other.getScoreMin();
        if (thisScoreMin == null ? otherScoreMin != null : !thisScoreMin.equals(otherScoreMin)) return false;
        final Object thisScoreMax = this.getScoreMax();
        final Object otherScoreMax = other.getScoreMax();
        if (thisScoreMax == null ? otherScoreMax != null : !thisScoreMax.equals(otherScoreMax)) return false;
        final Object thisSort = this.getSort();
        final Object otherSort = other.getSort();
        if (thisSort == null ? otherSort != null : !thisSort.equals(otherSort)) return false;
        final Object thisOrder = this.getOrder();
        final Object otherOrder = other.getOrder();
        if (thisOrder == null ? otherOrder != null : !thisOrder.equals(otherOrder)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectSearchQueryDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + this.getPage();
        result = result * PRIME + this.getSize();
        final Object hashYear = this.getYear();
        result = result * PRIME + (hashYear == null ? 43 : hashYear.hashCode());
        final Object hashWeekday = this.getWeekday();
        result = result * PRIME + (hashWeekday == null ? 43 : hashWeekday.hashCode());
        final Object hashQ = this.getQ();
        result = result * PRIME + (hashQ == null ? 43 : hashQ.hashCode());
        final Object hashTag = this.getTag();
        result = result * PRIME + (hashTag == null ? 43 : hashTag.hashCode());
        final Object hashScoreMin = this.getScoreMin();
        result = result * PRIME + (hashScoreMin == null ? 43 : hashScoreMin.hashCode());
        final Object hashScoreMax = this.getScoreMax();
        result = result * PRIME + (hashScoreMax == null ? 43 : hashScoreMax.hashCode());
        final Object hashSort = this.getSort();
        result = result * PRIME + (hashSort == null ? 43 : hashSort.hashCode());
        final Object hashOrder = this.getOrder();
        result = result * PRIME + (hashOrder == null ? 43 : hashOrder.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectSearchQueryDTO(q=" + this.getQ() + ", tag=" + this.getTag() + ", scoreMin=" + this.getScoreMin() + ", scoreMax=" + this.getScoreMax() + ", year=" + this.getYear() + ", weekday=" + this.getWeekday() + ", sort=" + this.getSort() + ", order=" + this.getOrder() + ", page=" + this.getPage() + ", size=" + this.getSize() + ")";
    }
}
