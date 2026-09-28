package top.zhaizz.client.model;

/**
 * 条目关联行（含关联条目标题）
 */
public class EvidenceRelationRow {
    /**
     * 关联条目标识
     */
    private Long subjectId;
    /**
     * 关联条目标识
     */
    private Long relatedSubjectId;
    /**
     * 关联条目的原始名称
     */
    private String relatedSubjectName;
    /**
     * 关联条目的中文名称
     */
    private String relatedSubjectNameCn;
    /**
     * 实体之间的关系类型
     */
    private String relation;

    /** 创建字段均为默认值的空关联行，供结果映射使用 */
    public EvidenceRelationRow() {
    }

    /**
     * 获取关联条目标识
     * @return 当前条目主键，未设置时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取关联条目标识
     * @return 被关联条目的主键，未设置时为 {@code null}
     */
    public Long getRelatedSubjectId() {
        return this.relatedSubjectId;
    }

    /**
     * 获取关联条目的原始名称
     * @return 被关联条目的原始语言名称，未设置时为 {@code null}
     */
    public String getRelatedSubjectName() {
        return this.relatedSubjectName;
    }

    /**
     * 获取关联条目的中文名称
     * @return 被关联条目的中文名称，未设置时为 {@code null}
     */
    public String getRelatedSubjectNameCn() {
        return this.relatedSubjectNameCn;
    }

    /**
     * 获取实体之间的关系类型
     * @return 两个条目之间的关系类型，未设置时为 {@code null}
     */
    public String getRelation() {
        return this.relation;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 新的当前条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换关联条目标识
     * @param relatedSubjectId 新的被关联条目主键，可为 {@code null}
     */
    public void setRelatedSubjectId(final Long relatedSubjectId) {
        this.relatedSubjectId = relatedSubjectId;
    }

    /**
     * 替换关联条目的原始名称
     * @param relatedSubjectName 新的被关联条目原始语言名称，可为 {@code null}
     */
    public void setRelatedSubjectName(final String relatedSubjectName) {
        this.relatedSubjectName = relatedSubjectName;
    }

    /**
     * 替换关联条目的中文名称
     * @param relatedSubjectNameCn 新的被关联条目中文名称，可为 {@code null}
     */
    public void setRelatedSubjectNameCn(final String relatedSubjectNameCn) {
        this.relatedSubjectNameCn = relatedSubjectNameCn;
    }

    /**
     * 替换实体之间的关系类型
     * @param relation 新的关系类型，可为 {@code null}
     */
    public void setRelation(final String relation) {
        this.relation = relation;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof EvidenceRelationRow)) return false;
        final EvidenceRelationRow other = (EvidenceRelationRow) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisRelatedSubjectId = this.getRelatedSubjectId();
        final Object otherRelatedSubjectId = other.getRelatedSubjectId();
        if (thisRelatedSubjectId == null ? otherRelatedSubjectId != null : !thisRelatedSubjectId.equals(otherRelatedSubjectId)) return false;
        final Object thisRelatedSubjectName = this.getRelatedSubjectName();
        final Object otherRelatedSubjectName = other.getRelatedSubjectName();
        if (thisRelatedSubjectName == null ? otherRelatedSubjectName != null : !thisRelatedSubjectName.equals(otherRelatedSubjectName)) return false;
        final Object thisRelatedSubjectNameCn = this.getRelatedSubjectNameCn();
        final Object otherRelatedSubjectNameCn = other.getRelatedSubjectNameCn();
        if (thisRelatedSubjectNameCn == null ? otherRelatedSubjectNameCn != null : !thisRelatedSubjectNameCn.equals(otherRelatedSubjectNameCn)) return false;
        final Object thisRelation = this.getRelation();
        final Object otherRelation = other.getRelation();
        if (thisRelation == null ? otherRelation != null : !thisRelation.equals(otherRelation)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof EvidenceRelationRow;
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
        final Object hashRelatedSubjectId = this.getRelatedSubjectId();
        result = result * PRIME + (hashRelatedSubjectId == null ? 43 : hashRelatedSubjectId.hashCode());
        final Object hashRelatedSubjectName = this.getRelatedSubjectName();
        result = result * PRIME + (hashRelatedSubjectName == null ? 43 : hashRelatedSubjectName.hashCode());
        final Object hashRelatedSubjectNameCn = this.getRelatedSubjectNameCn();
        result = result * PRIME + (hashRelatedSubjectNameCn == null ? 43 : hashRelatedSubjectNameCn.hashCode());
        final Object hashRelation = this.getRelation();
        result = result * PRIME + (hashRelation == null ? 43 : hashRelation.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "EvidenceRelationRow(subjectId=" + this.getSubjectId() + ", relatedSubjectId=" + this.getRelatedSubjectId() + ", relatedSubjectName=" + this.getRelatedSubjectName() + ", relatedSubjectNameCn=" + this.getRelatedSubjectNameCn() + ", relation=" + this.getRelation() + ")";
    }
}
