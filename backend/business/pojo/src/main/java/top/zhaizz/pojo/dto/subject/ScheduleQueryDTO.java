package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;

/**
 * 每周追番查询参数（weekday=-1 为哨兵：不过滤星期）
 */
public class ScheduleQueryDTO {
    /**
     * 播出星期（-1=不限, 0=周日 ... 6=周六）
     */
    @Min(value = -1, message = "星期范围 -1 到 6")
    @Max(value = 6, message = "星期范围 -1 到 6")
    private int weekday = -1; // 播出星期（-1=不限, 0=周日 ... 6=周六）
    /**
     * 年份（空=当前季度年份）
     */
    @Min(value = 1970, message = "年份不能早于1970")
    @Max(value = 2100, message = "年份不能晚于2100")
    private Integer year; // 年份（空=当前季度年份）
    /**
     * 季度（空=当前季度）
     */
    @Pattern(regexp = "spring|summer|autumn|winter", message = "季度仅允许: spring/summer/autumn/winter")
    private String quarter; // 季度（空=当前季度）
    /**
     * 页码
     */
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1; // 页码
    /**
     * 每页条数（原默认 50，刻意改为 20）
     */
    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20; // 每页条数（原默认 50，刻意改为 20）

    /** 创建星期不限、分页取默认值的空查询对象 */
    public ScheduleQueryDTO() {
    }

    /**
     * 获取播出星期
     * @return 播出星期，默认 -1 表示不限，其余取值 0=周日 至 6=周六
     */
    public int getWeekday() {
        return this.weekday;
    }

    /**
     * 获取年份
     * @return 播出年份，取值 1970~2100；为 {@code null} 时取当前季度年份
     */
    public Integer getYear() {
        return this.year;
    }

    /**
     * 获取季度
     * @return 季度标识 spring/summer/autumn/winter；为 {@code null} 时取当前季度
     */
    public String getQuarter() {
        return this.quarter;
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
     * 替换播出星期
     * @param weekday 播出星期，-1 表示不限，其余取值 0=周日 至 6=周六
     */
    public void setWeekday(final int weekday) {
        this.weekday = weekday;
    }

    /**
     * 替换年份
     * @param year 播出年份，取值 1970~2100；可为 {@code null} 表示取当前季度年份
     */
    public void setYear(final Integer year) {
        this.year = year;
    }

    /**
     * 替换季度
     * @param quarter 季度标识 spring/summer/autumn/winter；可为 {@code null} 表示取当前季度
     */
    public void setQuarter(final String quarter) {
        this.quarter = quarter;
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
        if (!(o instanceof ScheduleQueryDTO)) return false;
        final ScheduleQueryDTO other = (ScheduleQueryDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getWeekday() != other.getWeekday()) return false;
        if (this.getPage() != other.getPage()) return false;
        if (this.getSize() != other.getSize()) return false;
        final Object thisYear = this.getYear();
        final Object otherYear = other.getYear();
        if (thisYear == null ? otherYear != null : !thisYear.equals(otherYear)) return false;
        final Object thisQuarter = this.getQuarter();
        final Object otherQuarter = other.getQuarter();
        if (thisQuarter == null ? otherQuarter != null : !thisQuarter.equals(otherQuarter)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ScheduleQueryDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + this.getWeekday();
        result = result * PRIME + this.getPage();
        result = result * PRIME + this.getSize();
        final Object hashYear = this.getYear();
        result = result * PRIME + (hashYear == null ? 43 : hashYear.hashCode());
        final Object hashQuarter = this.getQuarter();
        result = result * PRIME + (hashQuarter == null ? 43 : hashQuarter.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ScheduleQueryDTO(weekday=" + this.getWeekday() + ", year=" + this.getYear() + ", quarter=" + this.getQuarter() + ", page=" + this.getPage() + ", size=" + this.getSize() + ")";
    }
}
