package top.zhaizz.pojo.vo.subject;

/**
 * 季度数量
 */
public class SeasonCountVO {
    /** 季度标识（如 2026-summer） */
    private String seasonKey;   // 季度标识（如 2026-summer）
    /** 该季度条目数 */
    private long count;         // 该季度条目数

    /** 创建字段均为默认值的空季度数量 */
    public SeasonCountVO() {
    }

    /**
     * 获取季度标识
     * @return 形如 {@code 2026-summer} 的季度标识；未提供时为 {@code null}
     */
    public String getSeasonKey() {
        return this.seasonKey;
    }

    /**
     * 获取该季度条目数
     * @return 该季度条目数量，未设置时默认为 {@code 0}
     */
    public long getCount() {
        return this.count;
    }

    /**
     * 替换季度标识
     * @param seasonKey 形如 {@code 2026-summer} 的季度标识，可为 {@code null}
     */
    public void setSeasonKey(final String seasonKey) {
        this.seasonKey = seasonKey;
    }

    /**
     * 替换该季度条目数
     * @param count 该季度条目数量，取值为基本类型 long
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
        if (!(o instanceof SeasonCountVO)) return false;
        final SeasonCountVO other = (SeasonCountVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getCount() != other.getCount()) return false;
        final Object thisSeasonKey = this.getSeasonKey();
        final Object otherSeasonKey = other.getSeasonKey();
        if (thisSeasonKey == null ? otherSeasonKey != null : !thisSeasonKey.equals(otherSeasonKey)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SeasonCountVO;
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
        final Object hashSeasonKey = this.getSeasonKey();
        result = result * PRIME + (hashSeasonKey == null ? 43 : hashSeasonKey.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SeasonCountVO(seasonKey=" + this.getSeasonKey() + ", count=" + this.getCount() + ")";
    }
}
