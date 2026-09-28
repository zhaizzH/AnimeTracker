package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 条目别名实体，保存条目的多语言别名及来源
 */
@TableName("subject_alias")
public class SubjectAlias {

    /** 别名 ID */
    private Long id;                    // 别名 ID

    /** 条目 ID */
    private Long subjectId;             // 条目 ID

    /** 别名 */
    private String name;                // 别名

    /** 语言 */
    private String language;            // 语言

    /** 来源 */
    private String source;              // 来源

    /** 上游是否仍然活跃 */
    private Boolean sourceActive;       // 上游是否仍然活跃

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public SubjectAlias() {
    }

    /**
     * 获取别名 ID
     * @return 别名 ID；未持久化或未提供时为 {@code null}
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
     * 获取别名
     * @return 别名；未持久化或未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取语言
     * @return 语言；未持久化或未提供时为 {@code null}
     */
    public String getLanguage() {
        return this.language;
    }

    /**
     * 获取来源
     * @return 来源；未持久化或未提供时为 {@code null}
     */
    public String getSource() {
        return this.source;
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
     * 获取更新时间
     * @return 更新时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getUpdatedAt() {
        return this.updatedAt;
    }

    /**
     * 替换别名 ID
     * @param id 别名 ID，可为 {@code null}
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
     * 替换别名
     * @param name 别名，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换语言
     * @param language 语言，可为 {@code null}
     */
    public void setLanguage(final String language) {
        this.language = language;
    }

    /**
     * 替换来源
     * @param source 来源，可为 {@code null}
     */
    public void setSource(final String source) {
        this.source = source;
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
     * 替换更新时间
     * @param updatedAt 更新时间，可为 {@code null}
     */
    public void setUpdatedAt(final LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectAlias)) return false;
        final SubjectAlias other = (SubjectAlias) o;
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
        final Object thisLanguage = this.getLanguage();
        final Object otherLanguage = other.getLanguage();
        if (thisLanguage == null ? otherLanguage != null : !thisLanguage.equals(otherLanguage)) return false;
        final Object thisSource = this.getSource();
        final Object otherSource = other.getSource();
        if (thisSource == null ? otherSource != null : !thisSource.equals(otherSource)) return false;
        final Object thisCreatedAt = this.getCreatedAt();
        final Object otherCreatedAt = other.getCreatedAt();
        if (thisCreatedAt == null ? otherCreatedAt != null : !thisCreatedAt.equals(otherCreatedAt)) return false;
        final Object thisUpdatedAt = this.getUpdatedAt();
        final Object otherUpdatedAt = other.getUpdatedAt();
        if (thisUpdatedAt == null ? otherUpdatedAt != null : !thisUpdatedAt.equals(otherUpdatedAt)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectAlias;
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
        final Object hashLanguage = this.getLanguage();
        result = result * PRIME + (hashLanguage == null ? 43 : hashLanguage.hashCode());
        final Object hashSource = this.getSource();
        result = result * PRIME + (hashSource == null ? 43 : hashSource.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        final Object hashUpdatedAt = this.getUpdatedAt();
        result = result * PRIME + (hashUpdatedAt == null ? 43 : hashUpdatedAt.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectAlias(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ", language=" + this.getLanguage() + ", source=" + this.getSource() + ", sourceActive=" + this.getSourceActive() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
