package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 旧版条目主创关联实体
 *
 * 新导入关系使用 subject_person_credit；该实体保留 subject_credit 的
 * 兼容读取契约，避免存量数据窗口内 ORM 映射缺失
 */
@TableName("subject_credit")
public class SubjectCredit {

    /** 记录或资源的唯一标识 */
    private Long id;

    /** 关联条目标识 */
    private Long subjectId;

    /** Bangumi 人物标识 */
    private Integer bangumiPersonId;

    /** 来源数据的原始名称 */
    private String name;

    /** 人员或角色在关系中的职务 */
    private String role;

    /** 主创类型：PERSON 为个人，ORGANIZATION 为组织 */
    private String creditType;

    /** 同级记录的排序序号 */
    private Integer sortOrder;

    /** 来源记录是否仍有效 */
    private Boolean sourceActive;

    /** 记录创建时间 */
    private LocalDateTime createdAt;

    /** 记录最后更新时间 */
    private LocalDateTime updatedAt;

    /** 创建各字段均为默认值的空实体 */
    public SubjectCredit() {
    }

    /**
     * 获取记录或资源的唯一标识
     * @return 记录或资源的唯一标识；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取关联条目标识
     * @return 关联条目标识；未持久化或未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取Bangumi 人物标识
     * @return Bangumi 人物标识；未持久化或未提供时为 {@code null}
     */
    public Integer getBangumiPersonId() {
        return this.bangumiPersonId;
    }

    /**
     * 获取来源数据的原始名称
     * @return 来源数据的原始名称；未持久化或未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取人员或角色在关系中的职务
     * @return 人员或角色在关系中的职务；未持久化或未提供时为 {@code null}
     */
    public String getRole() {
        return this.role;
    }

    /**
     * 获取主创类型：PERSON 为个人，ORGANIZATION 为组织
     * @return 主创类型：PERSON 为个人，ORGANIZATION 为组织；未持久化或未提供时为 {@code null}
     */
    public String getCreditType() {
        return this.creditType;
    }

    /**
     * 获取同级记录的排序序号
     * @return 同级记录的排序序号；未持久化或未提供时为 {@code null}
     */
    public Integer getSortOrder() {
        return this.sortOrder;
    }

    /**
     * 获取来源记录是否仍有效
     * @return 来源记录是否仍有效；未持久化或未提供时为 {@code null}
     */
    public Boolean getSourceActive() {
        return this.sourceActive;
    }

    /**
     * 获取记录创建时间
     * @return 记录创建时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 获取记录最后更新时间
     * @return 记录最后更新时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getUpdatedAt() {
        return this.updatedAt;
    }

    /**
     * 替换记录或资源的唯一标识
     * @param id 记录或资源的唯一标识，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 关联条目标识，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换Bangumi 人物标识
     * @param bangumiPersonId Bangumi 人物标识，可为 {@code null}
     */
    public void setBangumiPersonId(final Integer bangumiPersonId) {
        this.bangumiPersonId = bangumiPersonId;
    }

    /**
     * 替换来源数据的原始名称
     * @param name 来源数据的原始名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换人员或角色在关系中的职务
     * @param role 人员或角色在关系中的职务，可为 {@code null}
     */
    public void setRole(final String role) {
        this.role = role;
    }

    /**
     * 替换主创类型：PERSON 为个人，ORGANIZATION 为组织
     * @param creditType 主创类型：PERSON 为个人，ORGANIZATION 为组织，可为 {@code null}
     */
    public void setCreditType(final String creditType) {
        this.creditType = creditType;
    }

    /**
     * 替换同级记录的排序序号
     * @param sortOrder 同级记录的排序序号，可为 {@code null}
     */
    public void setSortOrder(final Integer sortOrder) {
        this.sortOrder = sortOrder;
    }

    /**
     * 替换来源记录是否仍有效
     * @param sourceActive 来源记录是否仍有效，可为 {@code null}
     */
    public void setSourceActive(final Boolean sourceActive) {
        this.sourceActive = sourceActive;
    }

    /**
     * 替换记录创建时间
     * @param createdAt 记录创建时间，可为 {@code null}
     */
    public void setCreatedAt(final LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 替换记录最后更新时间
     * @param updatedAt 记录最后更新时间，可为 {@code null}
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
        if (!(o instanceof SubjectCredit)) return false;
        final SubjectCredit other = (SubjectCredit) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisBangumiPersonId = this.getBangumiPersonId();
        final Object otherBangumiPersonId = other.getBangumiPersonId();
        if (thisBangumiPersonId == null ? otherBangumiPersonId != null : !thisBangumiPersonId.equals(otherBangumiPersonId)) return false;
        final Object thisSortOrder = this.getSortOrder();
        final Object otherSortOrder = other.getSortOrder();
        if (thisSortOrder == null ? otherSortOrder != null : !thisSortOrder.equals(otherSortOrder)) return false;
        final Object thisSourceActive = this.getSourceActive();
        final Object otherSourceActive = other.getSourceActive();
        if (thisSourceActive == null ? otherSourceActive != null : !thisSourceActive.equals(otherSourceActive)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisRole = this.getRole();
        final Object otherRole = other.getRole();
        if (thisRole == null ? otherRole != null : !thisRole.equals(otherRole)) return false;
        final Object thisCreditType = this.getCreditType();
        final Object otherCreditType = other.getCreditType();
        if (thisCreditType == null ? otherCreditType != null : !thisCreditType.equals(otherCreditType)) return false;
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
        return other instanceof SubjectCredit;
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
        final Object hashBangumiPersonId = this.getBangumiPersonId();
        result = result * PRIME + (hashBangumiPersonId == null ? 43 : hashBangumiPersonId.hashCode());
        final Object hashSortOrder = this.getSortOrder();
        result = result * PRIME + (hashSortOrder == null ? 43 : hashSortOrder.hashCode());
        final Object hashSourceActive = this.getSourceActive();
        result = result * PRIME + (hashSourceActive == null ? 43 : hashSourceActive.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashRole = this.getRole();
        result = result * PRIME + (hashRole == null ? 43 : hashRole.hashCode());
        final Object hashCreditType = this.getCreditType();
        result = result * PRIME + (hashCreditType == null ? 43 : hashCreditType.hashCode());
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
        return "SubjectCredit(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", bangumiPersonId=" + this.getBangumiPersonId() + ", name=" + this.getName() + ", role=" + this.getRole() + ", creditType=" + this.getCreditType() + ", sortOrder=" + this.getSortOrder() + ", sourceActive=" + this.getSourceActive() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
