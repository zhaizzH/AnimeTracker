package top.zhaizz.client.model;

/**
 * 条目的别名行
 */
public class EvidenceAliasRow {
    /**
     * 关联条目标识
     */
    private Long subjectId;
    /**
     * 来源数据的原始名称
     */
    private String name;

    /** 创建字段均为默认值的空别名行，供结果映射使用 */
    public EvidenceAliasRow() {
    }

    /**
     * 获取关联条目标识
     * @return 别名所属条目的主键，未设置时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取来源数据的原始名称
     * @return 来源中记录的别名文本，未设置时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 新的别名所属条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换来源数据的原始名称
     * @param name 新的别名文本，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof EvidenceAliasRow)) return false;
        final EvidenceAliasRow other = (EvidenceAliasRow) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
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
        return other instanceof EvidenceAliasRow;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
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
        return "EvidenceAliasRow(subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ")";
    }
}
