package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 用户追番收藏实体
 */
@TableName("user_collection")
public class UserCollection {

    /** 收藏ID */
    private Long id;                    // 收藏ID

    /** 用户ID */
    private Long userId;                // 用户ID

    /** 条目ID */
    private Long subjectId;             // 条目ID

    /** 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃 */
    private Integer type;               // 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃

    /** 评分（0~10, 0 表示未评分） */
    private Integer rate;               // 评分（0~10, 0 表示未评分）

    /** 看到第几集 */
    private Integer epStatus;           // 看到第几集

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public UserCollection() {
    }

    /**
     * 获取收藏ID
     * @return 收藏ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取用户ID
     * @return 用户ID；未持久化或未提供时为 {@code null}
     */
    public Long getUserId() {
        return this.userId;
    }

    /**
     * 获取条目ID
     * @return 条目ID；未持久化或未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
     * @return 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃；未持久化或未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取评分（0~10, 0 表示未评分）
     * @return 评分（0~10, 0 表示未评分）；未持久化或未提供时为 {@code null}
     */
    public Integer getRate() {
        return this.rate;
    }

    /**
     * 获取看到第几集
     * @return 看到第几集；未持久化或未提供时为 {@code null}
     */
    public Integer getEpStatus() {
        return this.epStatus;
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
     * 替换收藏ID
     * @param id 收藏ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换用户ID
     * @param userId 用户ID，可为 {@code null}
     */
    public void setUserId(final Long userId) {
        this.userId = userId;
    }

    /**
     * 替换条目ID
     * @param subjectId 条目ID，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
     * @param type 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃，可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换评分（0~10, 0 表示未评分）
     * @param rate 评分（0~10, 0 表示未评分），可为 {@code null}
     */
    public void setRate(final Integer rate) {
        this.rate = rate;
    }

    /**
     * 替换看到第几集
     * @param epStatus 看到第几集，可为 {@code null}
     */
    public void setEpStatus(final Integer epStatus) {
        this.epStatus = epStatus;
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
        if (!(o instanceof UserCollection)) return false;
        final UserCollection other = (UserCollection) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisUserId = this.getUserId();
        final Object otherUserId = other.getUserId();
        if (thisUserId == null ? otherUserId != null : !thisUserId.equals(otherUserId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisRate = this.getRate();
        final Object otherRate = other.getRate();
        if (thisRate == null ? otherRate != null : !thisRate.equals(otherRate)) return false;
        final Object thisEpStatus = this.getEpStatus();
        final Object otherEpStatus = other.getEpStatus();
        if (thisEpStatus == null ? otherEpStatus != null : !thisEpStatus.equals(otherEpStatus)) return false;
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
        return other instanceof UserCollection;
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
        final Object hashUserId = this.getUserId();
        result = result * PRIME + (hashUserId == null ? 43 : hashUserId.hashCode());
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashRate = this.getRate();
        result = result * PRIME + (hashRate == null ? 43 : hashRate.hashCode());
        final Object hashEpStatus = this.getEpStatus();
        result = result * PRIME + (hashEpStatus == null ? 43 : hashEpStatus.hashCode());
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
        return "UserCollection(id=" + this.getId() + ", userId=" + this.getUserId() + ", subjectId=" + this.getSubjectId() + ", type=" + this.getType() + ", rate=" + this.getRate() + ", epStatus=" + this.getEpStatus() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
