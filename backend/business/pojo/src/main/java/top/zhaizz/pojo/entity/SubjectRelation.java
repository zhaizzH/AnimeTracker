package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;

/**
 * 条目关联实体
 */
@TableName("subject_relation")
public class SubjectRelation {

    /** 关联ID */
    private Long id;                    // 关联ID

    /** 当前条目ID */
    private Long subjectId;             // 当前条目ID

    /** 关联条目ID */
    private Long relatedSubjectId;      // 关联条目ID

    /** 关联类型: prequel, sequel, side_story 等 */
    private String relation;            // 关联类型: prequel, sequel, side_story 等

    /** 创建各字段均为默认值的空实体 */
    public SubjectRelation() {
    }

    /**
     * 获取关联ID
     * @return 关联ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取当前条目ID
     * @return 当前条目ID；未持久化或未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取关联条目ID
     * @return 关联条目ID；未持久化或未提供时为 {@code null}
     */
    public Long getRelatedSubjectId() {
        return this.relatedSubjectId;
    }

    /**
     * 获取关联类型: prequel, sequel, side_story 等
     * @return 关联类型: prequel, sequel, side_story 等；未持久化或未提供时为 {@code null}
     */
    public String getRelation() {
        return this.relation;
    }

    /**
     * 替换关联ID
     * @param id 关联ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换当前条目ID
     * @param subjectId 当前条目ID，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换关联条目ID
     * @param relatedSubjectId 关联条目ID，可为 {@code null}
     */
    public void setRelatedSubjectId(final Long relatedSubjectId) {
        this.relatedSubjectId = relatedSubjectId;
    }

    /**
     * 替换关联类型: prequel, sequel, side_story 等
     * @param relation 关联类型: prequel, sequel, side_story 等，可为 {@code null}
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
        if (!(o instanceof SubjectRelation)) return false;
        final SubjectRelation other = (SubjectRelation) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisRelatedSubjectId = this.getRelatedSubjectId();
        final Object otherRelatedSubjectId = other.getRelatedSubjectId();
        if (thisRelatedSubjectId == null ? otherRelatedSubjectId != null : !thisRelatedSubjectId.equals(otherRelatedSubjectId)) return false;
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
        return other instanceof SubjectRelation;
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
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
        final Object hashRelatedSubjectId = this.getRelatedSubjectId();
        result = result * PRIME + (hashRelatedSubjectId == null ? 43 : hashRelatedSubjectId.hashCode());
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
        return "SubjectRelation(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", relatedSubjectId=" + this.getRelatedSubjectId() + ", relation=" + this.getRelation() + ")";
    }
}
