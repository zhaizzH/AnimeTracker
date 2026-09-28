package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;

/**
 * 条目标签关联实体
 */
@TableName("subject_tag")
public class SubjectTag {

    /** 标签关联ID */
    private Long id;                    // 标签关联ID

    /** 条目ID */
    private Long subjectId;             // 条目ID

    /** 标签名 */
    private String name;                // 标签名

    /** 该标签在此条目上的使用次数（来自 Bangumi API） */
    private Integer count;              // 该标签在此条目上的使用次数（来自 Bangumi API）

    /** 创建各字段均为默认值的空实体 */
    public SubjectTag() {
    }

    /**
     * 获取标签关联ID
     * @return 标签关联ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取条目ID
     * @return 条目ID；未持久化或未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取标签名
     * @return 标签名；未持久化或未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取该标签在此条目上的使用次数（来自 Bangumi API）
     * @return 该标签在此条目上的使用次数（来自 Bangumi API）；未持久化或未提供时为 {@code null}
     */
    public Integer getCount() {
        return this.count;
    }

    /**
     * 替换标签关联ID
     * @param id 标签关联ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换条目ID
     * @param subjectId 条目ID，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换标签名
     * @param name 标签名，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换该标签在此条目上的使用次数（来自 Bangumi API）
     * @param count 该标签在此条目上的使用次数（来自 Bangumi API），可为 {@code null}
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
        if (!(o instanceof SubjectTag)) return false;
        final SubjectTag other = (SubjectTag) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
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
        return other instanceof SubjectTag;
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
        return "SubjectTag(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ", count=" + this.getCount() + ")";
    }
}
