package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 通用搜索索引任务实体
 */
@TableName("search_index_job")
public class SearchIndexJob {

    /** 索引任务ID */
    private Long id;                        // 索引任务ID

    /** 实体类型: SUBJECT/EPISODE/PERSON/CHARACTER */
    private String entityKind;              // 实体类型: SUBJECT/EPISODE/PERSON/CHARACTER

    /** 本地实体ID */
    private Long entityId;                  // 本地实体ID

    /** 索引版本 */
    private String indexVersion;            // 索引版本

    /** 档案模板版本 */
    private String profileVersion;          // 档案模板版本

    /** 档案内容哈希 */
    private String contentHash;             // 档案内容哈希

    /** Embedding 供应商 */
    private String embeddingProvider;       // Embedding 供应商

    /** Embedding 模型 */
    private String embeddingModel;          // Embedding 模型

    /** 向量维度 */
    private Integer embeddingDimensions;    // 向量维度

    /** 任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE */
    private String status;                  // 任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE

    /** 尝试次数 */
    private Integer attempts;               // 尝试次数

    /** 最大尝试次数 */
    private Integer maxAttempts;            // 最大尝试次数

    /** 最近错误码 */
    private String lastErrorCode;           // 最近错误码

    /** 脱敏后的最近错误信息 */
    private String lastErrorMessage;        // 脱敏后的最近错误信息

    /** 下次重试时间 */
    private LocalDateTime nextRetryAt;      // 下次重试时间

    /** 认领时间 */
    private LocalDateTime claimedAt;        // 认领时间

    /** 完成索引时间 */
    private LocalDateTime indexedAt;        // 完成索引时间

    /** 创建时间 */
    private LocalDateTime createdAt;        // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;        // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public SearchIndexJob() {
    }

    /**
     * 获取索引任务ID
     * @return 索引任务ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取实体类型: SUBJECT/EPISODE/PERSON/CHARACTER
     * @return 实体类型: SUBJECT/EPISODE/PERSON/CHARACTER；未持久化或未提供时为 {@code null}
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
     * 获取索引版本
     * @return 索引版本；未持久化或未提供时为 {@code null}
     */
    public String getIndexVersion() {
        return this.indexVersion;
    }

    /**
     * 获取档案模板版本
     * @return 档案模板版本；未持久化或未提供时为 {@code null}
     */
    public String getProfileVersion() {
        return this.profileVersion;
    }

    /**
     * 获取档案内容哈希
     * @return 档案内容哈希；未持久化或未提供时为 {@code null}
     */
    public String getContentHash() {
        return this.contentHash;
    }

    /**
     * 获取Embedding 供应商
     * @return Embedding 供应商；未持久化或未提供时为 {@code null}
     */
    public String getEmbeddingProvider() {
        return this.embeddingProvider;
    }

    /**
     * 获取Embedding 模型
     * @return Embedding 模型；未持久化或未提供时为 {@code null}
     */
    public String getEmbeddingModel() {
        return this.embeddingModel;
    }

    /**
     * 获取向量维度
     * @return 向量维度；未持久化或未提供时为 {@code null}
     */
    public Integer getEmbeddingDimensions() {
        return this.embeddingDimensions;
    }

    /**
     * 获取任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE
     * @return 任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE；未持久化或未提供时为 {@code null}
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
     * 获取下次重试时间
     * @return 下次重试时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getNextRetryAt() {
        return this.nextRetryAt;
    }

    /**
     * 获取认领时间
     * @return 认领时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getClaimedAt() {
        return this.claimedAt;
    }

    /**
     * 获取完成索引时间
     * @return 完成索引时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getIndexedAt() {
        return this.indexedAt;
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
     * 替换索引任务ID
     * @param id 索引任务ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换实体类型: SUBJECT/EPISODE/PERSON/CHARACTER
     * @param entityKind 实体类型: SUBJECT/EPISODE/PERSON/CHARACTER，可为 {@code null}
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
     * 替换索引版本
     * @param indexVersion 索引版本，可为 {@code null}
     */
    public void setIndexVersion(final String indexVersion) {
        this.indexVersion = indexVersion;
    }

    /**
     * 替换档案模板版本
     * @param profileVersion 档案模板版本，可为 {@code null}
     */
    public void setProfileVersion(final String profileVersion) {
        this.profileVersion = profileVersion;
    }

    /**
     * 替换档案内容哈希
     * @param contentHash 档案内容哈希，可为 {@code null}
     */
    public void setContentHash(final String contentHash) {
        this.contentHash = contentHash;
    }

    /**
     * 替换Embedding 供应商
     * @param embeddingProvider Embedding 供应商，可为 {@code null}
     */
    public void setEmbeddingProvider(final String embeddingProvider) {
        this.embeddingProvider = embeddingProvider;
    }

    /**
     * 替换Embedding 模型
     * @param embeddingModel Embedding 模型，可为 {@code null}
     */
    public void setEmbeddingModel(final String embeddingModel) {
        this.embeddingModel = embeddingModel;
    }

    /**
     * 替换向量维度
     * @param embeddingDimensions 向量维度，可为 {@code null}
     */
    public void setEmbeddingDimensions(final Integer embeddingDimensions) {
        this.embeddingDimensions = embeddingDimensions;
    }

    /**
     * 替换任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE
     * @param status 任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE，可为 {@code null}
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
     * 替换下次重试时间
     * @param nextRetryAt 下次重试时间，可为 {@code null}
     */
    public void setNextRetryAt(final LocalDateTime nextRetryAt) {
        this.nextRetryAt = nextRetryAt;
    }

    /**
     * 替换认领时间
     * @param claimedAt 认领时间，可为 {@code null}
     */
    public void setClaimedAt(final LocalDateTime claimedAt) {
        this.claimedAt = claimedAt;
    }

    /**
     * 替换完成索引时间
     * @param indexedAt 完成索引时间，可为 {@code null}
     */
    public void setIndexedAt(final LocalDateTime indexedAt) {
        this.indexedAt = indexedAt;
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
        if (!(o instanceof SearchIndexJob)) return false;
        final SearchIndexJob other = (SearchIndexJob) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisEntityId = this.getEntityId();
        final Object otherEntityId = other.getEntityId();
        if (thisEntityId == null ? otherEntityId != null : !thisEntityId.equals(otherEntityId)) return false;
        final Object thisEmbeddingDimensions = this.getEmbeddingDimensions();
        final Object otherEmbeddingDimensions = other.getEmbeddingDimensions();
        if (thisEmbeddingDimensions == null ? otherEmbeddingDimensions != null : !thisEmbeddingDimensions.equals(otherEmbeddingDimensions)) return false;
        final Object thisAttempts = this.getAttempts();
        final Object otherAttempts = other.getAttempts();
        if (thisAttempts == null ? otherAttempts != null : !thisAttempts.equals(otherAttempts)) return false;
        final Object thisMaxAttempts = this.getMaxAttempts();
        final Object otherMaxAttempts = other.getMaxAttempts();
        if (thisMaxAttempts == null ? otherMaxAttempts != null : !thisMaxAttempts.equals(otherMaxAttempts)) return false;
        final Object thisEntityKind = this.getEntityKind();
        final Object otherEntityKind = other.getEntityKind();
        if (thisEntityKind == null ? otherEntityKind != null : !thisEntityKind.equals(otherEntityKind)) return false;
        final Object thisIndexVersion = this.getIndexVersion();
        final Object otherIndexVersion = other.getIndexVersion();
        if (thisIndexVersion == null ? otherIndexVersion != null : !thisIndexVersion.equals(otherIndexVersion)) return false;
        final Object thisProfileVersion = this.getProfileVersion();
        final Object otherProfileVersion = other.getProfileVersion();
        if (thisProfileVersion == null ? otherProfileVersion != null : !thisProfileVersion.equals(otherProfileVersion)) return false;
        final Object thisContentHash = this.getContentHash();
        final Object otherContentHash = other.getContentHash();
        if (thisContentHash == null ? otherContentHash != null : !thisContentHash.equals(otherContentHash)) return false;
        final Object thisEmbeddingProvider = this.getEmbeddingProvider();
        final Object otherEmbeddingProvider = other.getEmbeddingProvider();
        if (thisEmbeddingProvider == null ? otherEmbeddingProvider != null : !thisEmbeddingProvider.equals(otherEmbeddingProvider)) return false;
        final Object thisEmbeddingModel = this.getEmbeddingModel();
        final Object otherEmbeddingModel = other.getEmbeddingModel();
        if (thisEmbeddingModel == null ? otherEmbeddingModel != null : !thisEmbeddingModel.equals(otherEmbeddingModel)) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        final Object thisLastErrorCode = this.getLastErrorCode();
        final Object otherLastErrorCode = other.getLastErrorCode();
        if (thisLastErrorCode == null ? otherLastErrorCode != null : !thisLastErrorCode.equals(otherLastErrorCode)) return false;
        final Object thisLastErrorMessage = this.getLastErrorMessage();
        final Object otherLastErrorMessage = other.getLastErrorMessage();
        if (thisLastErrorMessage == null ? otherLastErrorMessage != null : !thisLastErrorMessage.equals(otherLastErrorMessage)) return false;
        final Object thisNextRetryAt = this.getNextRetryAt();
        final Object otherNextRetryAt = other.getNextRetryAt();
        if (thisNextRetryAt == null ? otherNextRetryAt != null : !thisNextRetryAt.equals(otherNextRetryAt)) return false;
        final Object thisClaimedAt = this.getClaimedAt();
        final Object otherClaimedAt = other.getClaimedAt();
        if (thisClaimedAt == null ? otherClaimedAt != null : !thisClaimedAt.equals(otherClaimedAt)) return false;
        final Object thisIndexedAt = this.getIndexedAt();
        final Object otherIndexedAt = other.getIndexedAt();
        if (thisIndexedAt == null ? otherIndexedAt != null : !thisIndexedAt.equals(otherIndexedAt)) return false;
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
        return other instanceof SearchIndexJob;
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
        final Object hashEmbeddingDimensions = this.getEmbeddingDimensions();
        result = result * PRIME + (hashEmbeddingDimensions == null ? 43 : hashEmbeddingDimensions.hashCode());
        final Object hashAttempts = this.getAttempts();
        result = result * PRIME + (hashAttempts == null ? 43 : hashAttempts.hashCode());
        final Object hashMaxAttempts = this.getMaxAttempts();
        result = result * PRIME + (hashMaxAttempts == null ? 43 : hashMaxAttempts.hashCode());
        final Object hashEntityKind = this.getEntityKind();
        result = result * PRIME + (hashEntityKind == null ? 43 : hashEntityKind.hashCode());
        final Object hashIndexVersion = this.getIndexVersion();
        result = result * PRIME + (hashIndexVersion == null ? 43 : hashIndexVersion.hashCode());
        final Object hashProfileVersion = this.getProfileVersion();
        result = result * PRIME + (hashProfileVersion == null ? 43 : hashProfileVersion.hashCode());
        final Object hashContentHash = this.getContentHash();
        result = result * PRIME + (hashContentHash == null ? 43 : hashContentHash.hashCode());
        final Object hashEmbeddingProvider = this.getEmbeddingProvider();
        result = result * PRIME + (hashEmbeddingProvider == null ? 43 : hashEmbeddingProvider.hashCode());
        final Object hashEmbeddingModel = this.getEmbeddingModel();
        result = result * PRIME + (hashEmbeddingModel == null ? 43 : hashEmbeddingModel.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        final Object hashLastErrorCode = this.getLastErrorCode();
        result = result * PRIME + (hashLastErrorCode == null ? 43 : hashLastErrorCode.hashCode());
        final Object hashLastErrorMessage = this.getLastErrorMessage();
        result = result * PRIME + (hashLastErrorMessage == null ? 43 : hashLastErrorMessage.hashCode());
        final Object hashNextRetryAt = this.getNextRetryAt();
        result = result * PRIME + (hashNextRetryAt == null ? 43 : hashNextRetryAt.hashCode());
        final Object hashClaimedAt = this.getClaimedAt();
        result = result * PRIME + (hashClaimedAt == null ? 43 : hashClaimedAt.hashCode());
        final Object hashIndexedAt = this.getIndexedAt();
        result = result * PRIME + (hashIndexedAt == null ? 43 : hashIndexedAt.hashCode());
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
        return "SearchIndexJob(id=" + this.getId() + ", entityKind=" + this.getEntityKind() + ", entityId=" + this.getEntityId() + ", indexVersion=" + this.getIndexVersion() + ", profileVersion=" + this.getProfileVersion() + ", contentHash=" + this.getContentHash() + ", embeddingProvider=" + this.getEmbeddingProvider() + ", embeddingModel=" + this.getEmbeddingModel() + ", embeddingDimensions=" + this.getEmbeddingDimensions() + ", status=" + this.getStatus() + ", attempts=" + this.getAttempts() + ", maxAttempts=" + this.getMaxAttempts() + ", lastErrorCode=" + this.getLastErrorCode() + ", lastErrorMessage=" + this.getLastErrorMessage() + ", nextRetryAt=" + this.getNextRetryAt() + ", claimedAt=" + this.getClaimedAt() + ", indexedAt=" + this.getIndexedAt() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
