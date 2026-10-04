package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 条目-人物主创关联实体
 *
 * <p>主创关系单表：已解析到 {@code person} 表时 {@code personId} 填 FK 且 {@code name} 为
 * NULL；未解析时 {@code personId} 为 NULL 且 {@code name} 存占位名。
 *
 * <p>表上的 {@code dedup_key} 是 VIRTUAL 生成列，仅供唯一索引去重，故意不映射为字段
 * —— 映射后 MyBatis-Plus 的 insert 会尝试写入生成列并报错。
 */
@TableName("subject_person_credit")
public class SubjectPersonCredit {

    /** 关联ID */
    private Long id;                    // 关联ID

    /** 条目ID */
    private Long subjectId;             // 条目ID

    /** 人物ID（未解析上游人物时为 NULL，此时用 name 存占位名） */
    private Long personId;              // 人物ID（未解析为 NULL）

    /** 占位名（personId 为 NULL 时填） */
    private String name;                // 占位名（personId 为 NULL 时填）

    /** 主创类型: PERSON=个人, ORGANIZATION=公司/组合 */
    private String creditType;          // 主创类型: PERSON 或 ORGANIZATION

    /** 职责（如导演、脚本） */
    private String role;                // 职责（如导演、脚本）

    /** 关系类型: MAIN=主要, SUB=次要 */
    private String relation;            // 关系类型: MAIN=主要, SUB=次要

    /** 来源排序 */
    private Integer sortOrder;          // 来源排序

    /** 上游是否仍然活跃 */
    private Boolean sourceActive;       // 上游是否仍然活跃

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public SubjectPersonCredit() {
    }

    /**
     * 获取关联ID
     * @return 关联ID；未持久化或未提供时为 {@code null}
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
     * 获取人物ID
     * @return 人物ID；**未解析上游人物时非空集合语义下为 {@code null}**，此时用 {@link #getName()} 的占位名
     */
    public Long getPersonId() {
        return this.personId;
    }

    /**
     * 获取占位名
     * @return 占位名；仅当 personId 为 {@code null} 时有值，已解析行返回 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取主创类型: PERSON=个人, ORGANIZATION=公司/组合
     * @return 主创类型；未持久化或未提供时为 {@code null}
     */
    public String getCreditType() {
        return this.creditType;
    }

    /**
     * 获取职责（如导演、脚本）
     * @return 职责（如导演、脚本）；未持久化或未提供时为 {@code null}
     */
    public String getRole() {
        return this.role;
    }

    /**
     * 获取关系类型: MAIN=主要, SUB=次要
     * @return 关系类型: MAIN=主要, SUB=次要；未持久化或未提供时为 {@code null}
     */
    public String getRelation() {
        return this.relation;
    }

    /**
     * 获取来源排序
     * @return 来源排序；未持久化或未提供时为 {@code null}
     */
    public Integer getSortOrder() {
        return this.sortOrder;
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
     * 替换关联ID
     * @param id 关联ID，可为 {@code null}
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
     * 替换人物ID
     * @param personId 人物ID，可为 {@code null}（未解析上游人物）
     */
    public void setPersonId(final Long personId) {
        this.personId = personId;
    }

    /**
     * 替换占位名
     * @param name 占位名，可为 {@code null}（已解析行应传 {@code null}）
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换主创类型: PERSON=个人, ORGANIZATION=公司/组合
     * @param creditType 主创类型，可为 {@code null}
     */
    public void setCreditType(final String creditType) {
        this.creditType = creditType;
    }

    /**
     * 替换职责（如导演、脚本）
     * @param role 职责（如导演、脚本），可为 {@code null}
     */
    public void setRole(final String role) {
        this.role = role;
    }

    /**
     * 替换关系类型: MAIN=主要, SUB=次要
     * @param relation 关系类型: MAIN=主要, SUB=次要，可为 {@code null}
     */
    public void setRelation(final String relation) {
        this.relation = relation;
    }

    /**
     * 替换来源排序
     * @param sortOrder 来源排序，可为 {@code null}
     */
    public void setSortOrder(final Integer sortOrder) {
        this.sortOrder = sortOrder;
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
        if (!(o instanceof SubjectPersonCredit)) return false;
        final SubjectPersonCredit other = (SubjectPersonCredit) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisPersonId = this.getPersonId();
        final Object otherPersonId = other.getPersonId();
        if (thisPersonId == null ? otherPersonId != null : !thisPersonId.equals(otherPersonId)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisCreditType = this.getCreditType();
        final Object otherCreditType = other.getCreditType();
        if (thisCreditType == null ? otherCreditType != null : !thisCreditType.equals(otherCreditType)) return false;
        final Object thisSortOrder = this.getSortOrder();
        final Object otherSortOrder = other.getSortOrder();
        if (thisSortOrder == null ? otherSortOrder != null : !thisSortOrder.equals(otherSortOrder)) return false;
        final Object thisSourceActive = this.getSourceActive();
        final Object otherSourceActive = other.getSourceActive();
        if (thisSourceActive == null ? otherSourceActive != null : !thisSourceActive.equals(otherSourceActive)) return false;
        final Object thisRole = this.getRole();
        final Object otherRole = other.getRole();
        if (thisRole == null ? otherRole != null : !thisRole.equals(otherRole)) return false;
        final Object thisRelation = this.getRelation();
        final Object otherRelation = other.getRelation();
        if (thisRelation == null ? otherRelation != null : !thisRelation.equals(otherRelation)) return false;
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
        return other instanceof SubjectPersonCredit;
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
        final Object hashPersonId = this.getPersonId();
        result = result * PRIME + (hashPersonId == null ? 43 : hashPersonId.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashCreditType = this.getCreditType();
        result = result * PRIME + (hashCreditType == null ? 43 : hashCreditType.hashCode());
        final Object hashSortOrder = this.getSortOrder();
        result = result * PRIME + (hashSortOrder == null ? 43 : hashSortOrder.hashCode());
        final Object hashSourceActive = this.getSourceActive();
        result = result * PRIME + (hashSourceActive == null ? 43 : hashSourceActive.hashCode());
        final Object hashRole = this.getRole();
        result = result * PRIME + (hashRole == null ? 43 : hashRole.hashCode());
        final Object hashRelation = this.getRelation();
        result = result * PRIME + (hashRelation == null ? 43 : hashRelation.hashCode());
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
        return "SubjectPersonCredit(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", personId=" + this.getPersonId() + ", name=" + this.getName() + ", creditType=" + this.getCreditType() + ", role=" + this.getRole() + ", relation=" + this.getRelation() + ", sortOrder=" + this.getSortOrder() + ", sourceActive=" + this.getSourceActive() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
