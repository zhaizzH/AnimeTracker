package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 条目官方标签关联实体，保存来自 Bangumi 的官方标签
 */
@TableName("subject_meta_tag")
public class SubjectMetaTag {

    /** 官方标签关联 ID */
    private Long id;                    // 官方标签关联 ID

    /** 条目 ID */
    private Long subjectId;             // 条目 ID

    /** 官方标签名 */
    private String name;                // 官方标签名

    /** 上游是否仍然活跃 */
    private Boolean sourceActive;       // 上游是否仍然活跃

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 创建各字段均为默认值的空实体 */
    public SubjectMetaTag() {
    }

    /**
     * 获取官方标签关联 ID
     * @return 官方标签关联 ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取条目 ID
     * @return 条目 ID；未持久化或未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取官方标签名
     * @return 官方标签名；未持久化或未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取上游是否仍然活跃
     * @return 上游是否仍然活跃；未持久化或未提供时为 {@code null}
     */
    public Boolean getSourceActive() {
        return this.sourceActive;
    }

    /**
     * 获取创建时间
     * @return 创建时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 替换官方标签关联 ID
     * @param id 官方标签关联 ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换条目 ID
     * @param subjectId 条目 ID，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换官方标签名
     * @param name 官方标签名，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换上游是否仍然活跃
     * @param sourceActive 上游是否仍然活跃，可为 {@code null}
     */
    public void setSourceActive(final Boolean sourceActive) {
        this.sourceActive = sourceActive;
    }

    /**
     * 替换创建时间
     * @param createdAt 创建时间，可为 {@code null}
     */
    public void setCreatedAt(final LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectMetaTag)) return false;
        final SubjectMetaTag other = (SubjectMetaTag) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisSourceActive = this.getSourceActive();
        final Object otherSourceActive = other.getSourceActive();
        if (thisSourceActive == null ? otherSourceActive != null : !thisSourceActive.equals(otherSourceActive)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisCreatedAt = this.getCreatedAt();
        final Object otherCreatedAt = other.getCreatedAt();
        if (thisCreatedAt == null ? otherCreatedAt != null : !thisCreatedAt.equals(otherCreatedAt)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectMetaTag;
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
        final Object hashSourceActive = this.getSourceActive();
        result = result * PRIME + (hashSourceActive == null ? 43 : hashSourceActive.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectMetaTag(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ", sourceActive=" + this.getSourceActive() + ", createdAt=" + this.getCreatedAt() + ")";
    }
}
