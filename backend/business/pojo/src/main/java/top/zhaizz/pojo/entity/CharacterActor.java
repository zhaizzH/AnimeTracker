package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 角色-声优关联实体（限定于特定作品）
 */
@TableName("character_actor")
public class CharacterActor {

    /** 关联ID */
    private Long id;                    // 关联ID

    /** 条目ID（声优关系限定于特定作品版本） */
    private Long subjectId;             // 条目ID（声优关系限定于特定作品版本）

    /** 角色ID */
    private Long characterId;           // 角色ID

    /** 声优人物ID */
    private Long personId;              // 声优人物ID

    /** 演员关系: VA=声优, ACTOR=真人演员 */
    private String actorRelation;       // 演员关系: VA=声优, ACTOR=真人演员

    /** 来源排序 */
    private Integer sortOrder;          // 来源排序

    /** 上游是否仍然活跃 */
    private Boolean sourceActive;       // 上游是否仍然活跃

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public CharacterActor() {
    }

    /**
     * 获取关联ID
     * @return 关联ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取条目ID（声优关系限定于特定作品版本）
     * @return 条目ID（声优关系限定于特定作品版本）；未持久化或未提供时为 {@code null}
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
     * 获取声优人物ID
     * @return 声优人物ID；未持久化或未提供时为 {@code null}
     */
    public Long getPersonId() {
        return this.personId;
    }

    /**
     * 获取演员关系: VA=声优, ACTOR=真人演员
     * @return 演员关系: VA=声优, ACTOR=真人演员；未持久化或未提供时为 {@code null}
     */
    public String getActorRelation() {
        return this.actorRelation;
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
     * 替换条目ID（声优关系限定于特定作品版本）
     * @param subjectId 条目ID（声优关系限定于特定作品版本），可为 {@code null}
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
     * 替换声优人物ID
     * @param personId 声优人物ID，可为 {@code null}
     */
    public void setPersonId(final Long personId) {
        this.personId = personId;
    }

    /**
     * 替换演员关系: VA=声优, ACTOR=真人演员
     * @param actorRelation 演员关系: VA=声优, ACTOR=真人演员，可为 {@code null}
     */
    public void setActorRelation(final String actorRelation) {
        this.actorRelation = actorRelation;
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
        if (!(o instanceof CharacterActor)) return false;
        final CharacterActor other = (CharacterActor) o;
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
        final Object thisPersonId = this.getPersonId();
        final Object otherPersonId = other.getPersonId();
        if (thisPersonId == null ? otherPersonId != null : !thisPersonId.equals(otherPersonId)) return false;
        final Object thisSortOrder = this.getSortOrder();
        final Object otherSortOrder = other.getSortOrder();
        if (thisSortOrder == null ? otherSortOrder != null : !thisSortOrder.equals(otherSortOrder)) return false;
        final Object thisSourceActive = this.getSourceActive();
        final Object otherSourceActive = other.getSourceActive();
        if (thisSourceActive == null ? otherSourceActive != null : !thisSourceActive.equals(otherSourceActive)) return false;
        final Object thisActorRelation = this.getActorRelation();
        final Object otherActorRelation = other.getActorRelation();
        if (thisActorRelation == null ? otherActorRelation != null : !thisActorRelation.equals(otherActorRelation)) return false;
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
        return other instanceof CharacterActor;
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
        final Object hashPersonId = this.getPersonId();
        result = result * PRIME + (hashPersonId == null ? 43 : hashPersonId.hashCode());
        final Object hashSortOrder = this.getSortOrder();
        result = result * PRIME + (hashSortOrder == null ? 43 : hashSortOrder.hashCode());
        final Object hashSourceActive = this.getSourceActive();
        result = result * PRIME + (hashSourceActive == null ? 43 : hashSourceActive.hashCode());
        final Object hashActorRelation = this.getActorRelation();
        result = result * PRIME + (hashActorRelation == null ? 43 : hashActorRelation.hashCode());
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
        return "CharacterActor(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", characterId=" + this.getCharacterId() + ", personId=" + this.getPersonId() + ", actorRelation=" + this.getActorRelation() + ", sortOrder=" + this.getSortOrder() + ", sourceActive=" + this.getSourceActive() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
