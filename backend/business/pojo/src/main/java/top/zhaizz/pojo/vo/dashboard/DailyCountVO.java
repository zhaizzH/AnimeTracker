package top.zhaizz.pojo.vo.dashboard;

import java.time.LocalDate;

/**
 * 日期计数行（内部聚合）
 */
public class DailyCountVO {

    /** 统计日期 */
    private LocalDate statDate; // 统计日期
    /** 该日期数量 */
    private long cnt; // 该日期数量

    /** 创建字段均为默认值的空计数行 */
    public DailyCountVO() {
    }

    /**
     * 获取统计日期
     * @return 聚合所对应的日期；未提供时为 {@code null}
     */
    public LocalDate getStatDate() {
        return this.statDate;
    }

    /**
     * 获取该日期数量
     * @return 该日期的新增数量，未设置时为 {@code 0}
     */
    public long getCnt() {
        return this.cnt;
    }

    /**
     * 替换统计日期
     * @param statDate 聚合所对应的日期，可为 {@code null}
     */
    public void setStatDate(final LocalDate statDate) {
        this.statDate = statDate;
    }

    /**
     * 替换该日期数量
     * @param cnt 该日期的新增数量
     */
    public void setCnt(final long cnt) {
        this.cnt = cnt;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof DailyCountVO)) return false;
        final DailyCountVO other = (DailyCountVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getCnt() != other.getCnt()) return false;
        final Object thisStatDate = this.getStatDate();
        final Object otherStatDate = other.getStatDate();
        if (thisStatDate == null ? otherStatDate != null : !thisStatDate.equals(otherStatDate)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof DailyCountVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashCnt = this.getCnt();
        result = result * PRIME + (int) (hashCnt >>> 32 ^ hashCnt);
        final Object hashStatDate = this.getStatDate();
        result = result * PRIME + (hashStatDate == null ? 43 : hashStatDate.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "DailyCountVO(statDate=" + this.getStatDate() + ", cnt=" + this.getCnt() + ")";
    }
}
