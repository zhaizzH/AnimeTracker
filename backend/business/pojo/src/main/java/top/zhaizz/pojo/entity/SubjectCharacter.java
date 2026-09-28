package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 条目-角色关联实体
 */
@TableName("subject_character")
public class SubjectCharacter {

    /** 关联ID */
    private Long id;                    // 关联ID

    /** 条目ID */
    private Long subjectId;             // 条目ID

    /** 角色ID */
    private Long characterId;           // 角色ID

    /** 角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串 */
    private String relation;            // 角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串

    /** 来源排序 */
    private Integer sortOrder;          // 来源排序

    /** 上游是否仍然活跃 */
    private Boolean sourceActive;       // 上游是否仍然活跃

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public SubjectCharacter() {
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
     * 获取角色ID
     * @return 角色ID；未持久化或未提供时为 {@code null}
     */
    public Long getCharacterId() {
        return this.characterId;
    }

    /**
     * 获取角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串
     * @return 角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串；未持久化或未提供时为 {@code null}
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
     * 替换角色ID
     * @param characterId 角色ID，可为 {@code null}
     */
    public void setCharacterId(final Long characterId) {
        this.characterId = characterId;
    }

    /**
     * 替换角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串
     * @param relation 角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串，可为 {@code null}
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
        if (!(o instanceof SubjectCharacter)) return false;
        final SubjectCharacter other = (SubjectCharacter) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisCharacterId = this.getCharacterId();
        final Object otherCharacterId = other.getCharacterId();
        if (thisCharacterId == null ? otherCharacterId != null : !thisCharacterId.equals(otherCharacterId)) return false;
        final Object thisSortOrder = this.getSortOrder();
        final Object otherSortOrder = other.getSortOrder();
        if (thisSortOrder == null ? otherSortOrder != null : !thisSortOrder.equals(otherSortOrder)) return false;
        final Object thisSourceActive = this.getSourceActive();
        final Object otherSourceActive = other.getSourceActive();
        if (thisSourceActive == null ? otherSourceActive != null : !thisSourceActive.equals(otherSourceActive)) return false;
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
        return other instanceof SubjectCharacter;
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
        final Object hashCharacterId = this.getCharacterId();
        result = result * PRIME + (hashCharacterId == null ? 43 : hashCharacterId.hashCode());
        final Object hashSortOrder = this.getSortOrder();
        result = result * PRIME + (hashSortOrder == null ? 43 : hashSortOrder.hashCode());
        final Object hashSourceActive = this.getSourceActive();
        result = result * PRIME + (hashSourceActive == null ? 43 : hashSourceActive.hashCode());
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
        return "SubjectCharacter(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", characterId=" + this.getCharacterId() + ", relation=" + this.getRelation() + ", sortOrder=" + this.getSortOrder() + ", sourceActive=" + this.getSourceActive() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
