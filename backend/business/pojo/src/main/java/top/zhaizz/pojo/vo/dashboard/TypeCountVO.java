package top.zhaizz.pojo.vo.dashboard;

/**
 * 收藏类型分布
 */
public class TypeCountVO {

    /** 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃 */
    private Integer type; // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    /** 该类型数量 */
    private long count; // 该类型数量

    /** 创建字段均为默认值的空类型分布项 */
    public TypeCountVO() {
    }

    /**
     * 获取收藏类型
     * @return 收藏类型：1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃；未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取该类型数量
     * @return 该收藏类型对应的记录数量，未设置时为 {@code 0}
     */
    public long getCount() {
        return this.count;
    }

    /**
     * 替换收藏类型
     * @param type 收藏类型：1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃，可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换该类型数量
     * @param count 该收藏类型对应的记录数量
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
        if (!(o instanceof TypeCountVO)) return false;
        final TypeCountVO other = (TypeCountVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getCount() != other.getCount()) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof TypeCountVO;
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
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "TypeCountVO(type=" + this.getType() + ", count=" + this.getCount() + ")";
    }
}
