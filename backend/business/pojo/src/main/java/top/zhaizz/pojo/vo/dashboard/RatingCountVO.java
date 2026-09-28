package top.zhaizz.pojo.vo.dashboard;

/**
 * 评分分布
 */
public class RatingCountVO {

    /** 评分值 1~10 */
    private Integer rate; // 评分值 1~10
    /** 该评分数量 */
    private long count; // 该评分数量

    /** 创建字段均为默认值的空评分分布项 */
    public RatingCountVO() {
    }

    /**
     * 获取评分值
     * @return 评分值（1~10）；未提供时为 {@code null}
     */
    public Integer getRate() {
        return this.rate;
    }

    /**
     * 获取该评分数量
     * @return 该评分对应的收藏数量，未设置时为 {@code 0}
     */
    public long getCount() {
        return this.count;
    }

    /**
     * 替换评分值
     * @param rate 评分值（1~10），可为 {@code null}
     */
    public void setRate(final Integer rate) {
        this.rate = rate;
    }

    /**
     * 替换该评分数量
     * @param count 该评分对应的收藏数量
     */
    public void setCount(final long count) {
        this.count = count;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof RatingCountVO)) return false;
        final RatingCountVO other = (RatingCountVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getCount() != other.getCount()) return false;
        final Object thisRate = this.getRate();
        final Object otherRate = other.getRate();
        if (thisRate == null ? otherRate != null : !thisRate.equals(otherRate)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof RatingCountVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashCount = this.getCount();
        result = result * PRIME + (int) (hashCount >>> 32 ^ hashCount);
        final Object hashRate = this.getRate();
        result = result * PRIME + (hashRate == null ? 43 : hashRate.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "RatingCountVO(rate=" + this.getRate() + ", count=" + this.getCount() + ")";
    }
}
