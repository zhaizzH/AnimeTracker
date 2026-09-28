package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 实体详情渐进回填任务实体
 */
@TableName("entity_detail_job")
public class EntityDetailJob {

    /** 任务ID */
    private Long id;                        // 任务ID

    /** 实体类型: PERSON/CHARACTER */
    private String entityKind;              // 实体类型: PERSON/CHARACTER

    /** 本地实体ID */
    private Long entityId;                  // 本地实体ID

    /** Bangumi 上游ID */
    private Integer sourceId;               // Bangumi 上游ID

    /** 任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED */
    private String status;                  // 任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED

    /** 尝试次数 */
    private Integer attempts;               // 尝试次数

    /** 最大尝试次数 */
    private Integer maxAttempts;            // 最大尝试次数

    /** 下次重试时间 */
    private LocalDateTime nextRetryAt;      // 下次重试时间

    /** 最近错误码 */
    private String lastErrorCode;           // 最近错误码

    /** 脱敏后的最近错误信息 */
    private String lastErrorMessage;        // 脱敏后的最近错误信息

    /** 回填断点 JSON */
    private String checkpointJson;          // 回填断点 JSON

    /** 完成时的来源数据哈希 */
    private String sourceHash;              // 完成时的来源数据哈希

    /** 认领时间 */
    private LocalDateTime claimedAt;        // 认领时间

    /** 完成时间 */
    private LocalDateTime completedAt;      // 完成时间

    /** 创建时间 */
    private LocalDateTime createdAt;        // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;        // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public EntityDetailJob() {
    }

    /**
     * 获取任务ID
     * @return 任务ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取实体类型: PERSON/CHARACTER
     * @return 实体类型: PERSON/CHARACTER；未持久化或未提供时为 {@code null}
     */
    public String getEntityKind() {
        return this.entityKind;
    }

    /**
     * 获取本地实体ID
     * @return 本地实体ID；未持久化或未提供时为 {@code null}
     */
    public Long getEntityId() {
        return this.entityId;
    }

    /**
     * 获取Bangumi 上游ID
     * @return Bangumi 上游ID；未持久化或未提供时为 {@code null}
     */
    public Integer getSourceId() {
        return this.sourceId;
    }

    /**
     * 获取任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED
     * @return 任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED；未持久化或未提供时为 {@code null}
     */
    public String getStatus() {
        return this.status;
    }

    /**
     * 获取尝试次数
     * @return 尝试次数；未持久化或未提供时为 {@code null}
     */
    public Integer getAttempts() {
        return this.attempts;
    }

    /**
     * 获取最大尝试次数
     * @return 最大尝试次数；未持久化或未提供时为 {@code null}
     */
    public Integer getMaxAttempts() {
        return this.maxAttempts;
    }

    /**
     * 获取下次重试时间
     * @return 下次重试时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getNextRetryAt() {
        return this.nextRetryAt;
    }

    /**
     * 获取最近错误码
     * @return 最近错误码；未持久化或未提供时为 {@code null}
     */
    public String getLastErrorCode() {
        return this.lastErrorCode;
    }

    /**
     * 获取脱敏后的最近错误信息
     * @return 脱敏后的最近错误信息；未持久化或未提供时为 {@code null}
     */
    public String getLastErrorMessage() {
        return this.lastErrorMessage;
    }

    /**
     * 获取回填断点 JSON
     * @return 回填断点 JSON；未持久化或未提供时为 {@code null}
     */
    public String getCheckpointJson() {
        return this.checkpointJson;
    }

    /**
     * 获取完成时的来源数据哈希
     * @return 完成时的来源数据哈希；未持久化或未提供时为 {@code null}
     */
    public String getSourceHash() {
        return this.sourceHash;
    }

    /**
     * 获取认领时间
     * @return 认领时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getClaimedAt() {
        return this.claimedAt;
    }

    /**
     * 获取完成时间
     * @return 完成时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getCompletedAt() {
        return this.completedAt;
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
     * 替换任务ID
     * @param id 任务ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换实体类型: PERSON/CHARACTER
     * @param entityKind 实体类型: PERSON/CHARACTER，可为 {@code null}
     */
    public void setEntityKind(final String entityKind) {
        this.entityKind = entityKind;
    }

    /**
     * 替换本地实体ID
     * @param entityId 本地实体ID，可为 {@code null}
     */
    public void setEntityId(final Long entityId) {
        this.entityId = entityId;
    }

    /**
     * 替换Bangumi 上游ID
     * @param sourceId Bangumi 上游ID，可为 {@code null}
     */
    public void setSourceId(final Integer sourceId) {
        this.sourceId = sourceId;
    }

    /**
     * 替换任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED
     * @param status 任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED，可为 {@code null}
     */
    public void setStatus(final String status) {
        this.status = status;
    }

    /**
     * 替换尝试次数
     * @param attempts 尝试次数，可为 {@code null}
     */
    public void setAttempts(final Integer attempts) {
        this.attempts = attempts;
    }

    /**
     * 替换最大尝试次数
     * @param maxAttempts 最大尝试次数，可为 {@code null}
     */
    public void setMaxAttempts(final Integer maxAttempts) {
        this.maxAttempts = maxAttempts;
    }

    /**
     * 替换下次重试时间
     * @param nextRetryAt 下次重试时间，可为 {@code null}
     */
    public void setNextRetryAt(final LocalDateTime nextRetryAt) {
        this.nextRetryAt = nextRetryAt;
    }

    /**
     * 替换最近错误码
     * @param lastErrorCode 最近错误码，可为 {@code null}
     */
    public void setLastErrorCode(final String lastErrorCode) {
        this.lastErrorCode = lastErrorCode;
    }

    /**
     * 替换脱敏后的最近错误信息
     * @param lastErrorMessage 脱敏后的最近错误信息，可为 {@code null}
     */
    public void setLastErrorMessage(final String lastErrorMessage) {
        this.lastErrorMessage = lastErrorMessage;
    }

    /**
     * 替换回填断点 JSON
     * @param checkpointJson 回填断点 JSON，可为 {@code null}
     */
    public void setCheckpointJson(final String checkpointJson) {
        this.checkpointJson = checkpointJson;
    }

    /**
     * 替换完成时的来源数据哈希
     * @param sourceHash 完成时的来源数据哈希，可为 {@code null}
     */
    public void setSourceHash(final String sourceHash) {
        this.sourceHash = sourceHash;
    }

    /**
     * 替换认领时间
     * @param claimedAt 认领时间，可为 {@code null}
     */
    public void setClaimedAt(final LocalDateTime claimedAt) {
        this.claimedAt = claimedAt;
    }

    /**
     * 替换完成时间
     * @param completedAt 完成时间，可为 {@code null}
     */
    public void setCompletedAt(final LocalDateTime completedAt) {
        this.completedAt = completedAt;
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
        if (!(o instanceof EntityDetailJob)) return false;
        final EntityDetailJob other = (EntityDetailJob) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisEntityId = this.getEntityId();
        final Object otherEntityId = other.getEntityId();
        if (thisEntityId == null ? otherEntityId != null : !thisEntityId.equals(otherEntityId)) return false;
        final Object thisSourceId = this.getSourceId();
        final Object otherSourceId = other.getSourceId();
        if (thisSourceId == null ? otherSourceId != null : !thisSourceId.equals(otherSourceId)) return false;
        final Object thisAttempts = this.getAttempts();
        final Object otherAttempts = other.getAttempts();
        if (thisAttempts == null ? otherAttempts != null : !thisAttempts.equals(otherAttempts)) return false;
        final Object thisMaxAttempts = this.getMaxAttempts();
        final Object otherMaxAttempts = other.getMaxAttempts();
        if (thisMaxAttempts == null ? otherMaxAttempts != null : !thisMaxAttempts.equals(otherMaxAttempts)) return false;
        final Object thisEntityKind = this.getEntityKind();
        final Object otherEntityKind = other.getEntityKind();
        if (thisEntityKind == null ? otherEntityKind != null : !thisEntityKind.equals(otherEntityKind)) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        final Object thisNextRetryAt = this.getNextRetryAt();
        final Object otherNextRetryAt = other.getNextRetryAt();
        if (thisNextRetryAt == null ? otherNextRetryAt != null : !thisNextRetryAt.equals(otherNextRetryAt)) return false;
        final Object thisLastErrorCode = this.getLastErrorCode();
        final Object otherLastErrorCode = other.getLastErrorCode();
        if (thisLastErrorCode == null ? otherLastErrorCode != null : !thisLastErrorCode.equals(otherLastErrorCode)) return false;
        final Object thisLastErrorMessage = this.getLastErrorMessage();
        final Object otherLastErrorMessage = other.getLastErrorMessage();
        if (thisLastErrorMessage == null ? otherLastErrorMessage != null : !thisLastErrorMessage.equals(otherLastErrorMessage)) return false;
        final Object thisCheckpointJson = this.getCheckpointJson();
        final Object otherCheckpointJson = other.getCheckpointJson();
        if (thisCheckpointJson == null ? otherCheckpointJson != null : !thisCheckpointJson.equals(otherCheckpointJson)) return false;
        final Object thisSourceHash = this.getSourceHash();
        final Object otherSourceHash = other.getSourceHash();
        if (thisSourceHash == null ? otherSourceHash != null : !thisSourceHash.equals(otherSourceHash)) return false;
        final Object thisClaimedAt = this.getClaimedAt();
        final Object otherClaimedAt = other.getClaimedAt();
        if (thisClaimedAt == null ? otherClaimedAt != null : !thisClaimedAt.equals(otherClaimedAt)) return false;
        final Object thisCompletedAt = this.getCompletedAt();
        final Object otherCompletedAt = other.getCompletedAt();
        if (thisCompletedAt == null ? otherCompletedAt != null : !thisCompletedAt.equals(otherCompletedAt)) return false;
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
        return other instanceof EntityDetailJob;
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
        final Object hashEntityId = this.getEntityId();
        result = result * PRIME + (hashEntityId == null ? 43 : hashEntityId.hashCode());
        final Object hashSourceId = this.getSourceId();
        result = result * PRIME + (hashSourceId == null ? 43 : hashSourceId.hashCode());
        final Object hashAttempts = this.getAttempts();
        result = result * PRIME + (hashAttempts == null ? 43 : hashAttempts.hashCode());
        final Object hashMaxAttempts = this.getMaxAttempts();
        result = result * PRIME + (hashMaxAttempts == null ? 43 : hashMaxAttempts.hashCode());
        final Object hashEntityKind = this.getEntityKind();
        result = result * PRIME + (hashEntityKind == null ? 43 : hashEntityKind.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        final Object hashNextRetryAt = this.getNextRetryAt();
        result = result * PRIME + (hashNextRetryAt == null ? 43 : hashNextRetryAt.hashCode());
        final Object hashLastErrorCode = this.getLastErrorCode();
        result = result * PRIME + (hashLastErrorCode == null ? 43 : hashLastErrorCode.hashCode());
        final Object hashLastErrorMessage = this.getLastErrorMessage();
        result = result * PRIME + (hashLastErrorMessage == null ? 43 : hashLastErrorMessage.hashCode());
        final Object hashCheckpointJson = this.getCheckpointJson();
        result = result * PRIME + (hashCheckpointJson == null ? 43 : hashCheckpointJson.hashCode());
        final Object hashSourceHash = this.getSourceHash();
        result = result * PRIME + (hashSourceHash == null ? 43 : hashSourceHash.hashCode());
        final Object hashClaimedAt = this.getClaimedAt();
        result = result * PRIME + (hashClaimedAt == null ? 43 : hashClaimedAt.hashCode());
        final Object hashCompletedAt = this.getCompletedAt();
        result = result * PRIME + (hashCompletedAt == null ? 43 : hashCompletedAt.hashCode());
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
        return "EntityDetailJob(id=" + this.getId() + ", entityKind=" + this.getEntityKind() + ", entityId=" + this.getEntityId() + ", sourceId=" + this.getSourceId() + ", status=" + this.getStatus() + ", attempts=" + this.getAttempts() + ", maxAttempts=" + this.getMaxAttempts() + ", nextRetryAt=" + this.getNextRetryAt() + ", lastErrorCode=" + this.getLastErrorCode() + ", lastErrorMessage=" + this.getLastErrorMessage() + ", checkpointJson=" + this.getCheckpointJson() + ", sourceHash=" + this.getSourceHash() + ", claimedAt=" + this.getClaimedAt() + ", completedAt=" + this.getCompletedAt() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
