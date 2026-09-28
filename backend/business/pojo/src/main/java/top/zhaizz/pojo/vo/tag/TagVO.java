package top.zhaizz.pojo.vo.tag;

/**
 * 标签信息 VO
 */
public class TagVO {

    /** 标签ID */
    private Long id;            // 标签ID
    /** 标签名 */
    private String name;        // 标签名
    /** 该标签在此条目上的使用次数 */
    private Integer count;      // 该标签在此条目上的使用次数

    /** 创建字段均为默认值的空标签信息 */
    public TagVO() {
    }

    /**
     * 获取标签ID
     * @return 标签主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取标签名
     * @return 标签名称；未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取该标签在此条目上的使用次数
     * @return 使用次数；未提供时为 {@code null}
     */
    public Integer getCount() {
        return this.count;
    }

    /**
     * 替换标签ID
     * @param id 标签主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换标签名
     * @param name 标签名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换该标签在此条目上的使用次数
     * @param count 使用次数，可为 {@code null}
     */
    public void setCount(final Integer count) {
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
        if (!(o instanceof TagVO)) return false;
        final TagVO other = (TagVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisCount = this.getCount();
        final Object otherCount = other.getCount();
        if (thisCount == null ? otherCount != null : !thisCount.equals(otherCount)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof TagVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashId = this.getId();
        result = result * PRIME + (hashId == null ? 43 : hashId.hashCode());
        final Object hashCount = this.getCount();
        result = result * PRIME + (hashCount == null ? 43 : hashCount.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "TagVO(id=" + this.getId() + ", name=" + this.getName() + ", count=" + this.getCount() + ")";
    }
}
