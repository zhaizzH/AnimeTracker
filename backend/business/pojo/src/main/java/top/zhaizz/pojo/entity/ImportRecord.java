package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 导入记录实体
 */
@TableName("import_record")
public class ImportRecord {

    /** 记录ID */
    private Long id;                    // 记录ID

    /** 导入模式: full, recent, season, since */
    private String mode;                // 导入模式: full, recent, season, since

    /** 季度标识（如 2026-spring） */
    private String seasonKey;           // 季度标识（如 2026-spring）

    /** 开始时间 */
    private LocalDateTime startedAt;    // 开始时间

    /** 完成时间 */
    private LocalDateTime completedAt;  // 完成时间

    /** 状态: RUNNING, COMPLETED, FAILED */
    private String status;              // 状态: RUNNING, COMPLETED, FAILED

    /** 本次导入的条目数 */
    private int subjectCount;           // 本次导入的条目数

    /** 错误信息（失败时记录） */
    private String errorMessage;        // 错误信息（失败时记录）

    /** 导入断点 JSON */
    private String checkpointJson;      // 导入断点 JSON

    /** 已扫描条目数 */
    private Integer scannedCount;       // 已扫描条目数

    /** 成功处理条目数 */
    private Integer successCount;       // 成功处理条目数

    /** 失败处理条目数 */
    private Integer failureCount;       // 失败处理条目数

    /** 跳过条目数 */
    private Integer skippedCount;       // 跳过条目数

    /** 源数据快照时间 */
    private LocalDateTime sourceSnapshotAt; // 源数据快照时间

    /** 最近任务心跳时间 */
    private LocalDateTime heartbeatAt;  // 最近任务心跳时间

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 创建各字段均为默认值的空实体 */
    public ImportRecord() {
    }

    /**
     * 获取记录ID
     * @return 记录ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取导入模式: full, recent, season, since
     * @return 导入模式: full, recent, season, since；未持久化或未提供时为 {@code null}
     */
    public String getMode() {
        return this.mode;
    }

    /**
     * 获取季度标识（如 2026-spring）
     * @return 季度标识（如 2026-spring）；未持久化或未提供时为 {@code null}
     */
    public String getSeasonKey() {
        return this.seasonKey;
    }

    /**
     * 获取开始时间
     * @return 开始时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getStartedAt() {
        return this.startedAt;
    }

    /**
     * 获取完成时间
     * @return 完成时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getCompletedAt() {
        return this.completedAt;
    }

    /**
     * 获取状态: RUNNING, COMPLETED, FAILED
     * @return 状态: RUNNING, COMPLETED, FAILED；未持久化或未提供时为 {@code null}
     */
    public String getStatus() {
        return this.status;
    }

    /**
     * 获取本次导入的条目数
     * @return 本次导入的条目数；无记录时表现为 {@code 0}
     */
    public int getSubjectCount() {
        return this.subjectCount;
    }

    /**
     * 获取错误信息（失败时记录）
     * @return 错误信息（失败时记录）；未持久化或未提供时为 {@code null}
     */
    public String getErrorMessage() {
        return this.errorMessage;
    }

    /**
     * 获取导入断点 JSON
     * @return 导入断点 JSON；未持久化或未提供时为 {@code null}
     */
    public String getCheckpointJson() {
        return this.checkpointJson;
    }

    /**
     * 获取已扫描条目数
     * @return 已扫描条目数；未持久化或未提供时为 {@code null}
     */
    public Integer getScannedCount() {
        return this.scannedCount;
    }

    /**
     * 获取成功处理条目数
     * @return 成功处理条目数；未持久化或未提供时为 {@code null}
     */
    public Integer getSuccessCount() {
        return this.successCount;
    }

    /**
     * 获取失败处理条目数
     * @return 失败处理条目数；未持久化或未提供时为 {@code null}
     */
    public Integer getFailureCount() {
        return this.failureCount;
    }

    /**
     * 获取跳过条目数
     * @return 跳过条目数；未持久化或未提供时为 {@code null}
     */
    public Integer getSkippedCount() {
        return this.skippedCount;
    }

    /**
     * 获取源数据快照时间
     * @return 源数据快照时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getSourceSnapshotAt() {
        return this.sourceSnapshotAt;
    }

    /**
     * 获取最近任务心跳时间
     * @return 最近任务心跳时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getHeartbeatAt() {
        return this.heartbeatAt;
    }

    /**
     * 获取创建时间
     * @return 创建时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 替换记录ID
     * @param id 记录ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换导入模式: full, recent, season, since
     * @param mode 导入模式: full, recent, season, since，可为 {@code null}
     */
    public void setMode(final String mode) {
        this.mode = mode;
    }

    /**
     * 替换季度标识（如 2026-spring）
     * @param seasonKey 季度标识（如 2026-spring），可为 {@code null}
     */
    public void setSeasonKey(final String seasonKey) {
        this.seasonKey = seasonKey;
    }

    /**
     * 替换开始时间
     * @param startedAt 开始时间，可为 {@code null}
     */
    public void setStartedAt(final LocalDateTime startedAt) {
        this.startedAt = startedAt;
    }

    /**
     * 替换完成时间
     * @param completedAt 完成时间，可为 {@code null}
     */
    public void setCompletedAt(final LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }

    /**
     * 替换状态: RUNNING, COMPLETED, FAILED
     * @param status 状态: RUNNING, COMPLETED, FAILED，可为 {@code null}
     */
    public void setStatus(final String status) {
        this.status = status;
    }

    /**
     * 替换本次导入的条目数
     * @param subjectCount 本次导入的条目数，为 {@code int} 基本类型
     */
    public void setSubjectCount(final int subjectCount) {
        this.subjectCount = subjectCount;
    }

    /**
     * 替换错误信息（失败时记录）
     * @param errorMessage 错误信息（失败时记录），可为 {@code null}
     */
    public void setErrorMessage(final String errorMessage) {
        this.errorMessage = errorMessage;
    }

    /**
     * 替换导入断点 JSON
     * @param checkpointJson 导入断点 JSON，可为 {@code null}
     */
    public void setCheckpointJson(final String checkpointJson) {
        this.checkpointJson = checkpointJson;
    }

    /**
     * 替换已扫描条目数
     * @param scannedCount 已扫描条目数，可为 {@code null}
     */
    public void setScannedCount(final Integer scannedCount) {
        this.scannedCount = scannedCount;
    }

    /**
     * 替换成功处理条目数
     * @param successCount 成功处理条目数，可为 {@code null}
     */
    public void setSuccessCount(final Integer successCount) {
        this.successCount = successCount;
    }

    /**
     * 替换失败处理条目数
     * @param failureCount 失败处理条目数，可为 {@code null}
     */
    public void setFailureCount(final Integer failureCount) {
        this.failureCount = failureCount;
    }

    /**
     * 替换跳过条目数
     * @param skippedCount 跳过条目数，可为 {@code null}
     */
    public void setSkippedCount(final Integer skippedCount) {
        this.skippedCount = skippedCount;
    }

    /**
     * 替换源数据快照时间
     * @param sourceSnapshotAt 源数据快照时间，可为 {@code null}
     */
    public void setSourceSnapshotAt(final LocalDateTime sourceSnapshotAt) {
        this.sourceSnapshotAt = sourceSnapshotAt;
    }

    /**
     * 替换最近任务心跳时间
     * @param heartbeatAt 最近任务心跳时间，可为 {@code null}
     */
    public void setHeartbeatAt(final LocalDateTime heartbeatAt) {
        this.heartbeatAt = heartbeatAt;
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
        if (!(o instanceof ImportRecord)) return false;
        final ImportRecord other = (ImportRecord) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getSubjectCount() != other.getSubjectCount()) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisScannedCount = this.getScannedCount();
        final Object otherScannedCount = other.getScannedCount();
        if (thisScannedCount == null ? otherScannedCount != null : !thisScannedCount.equals(otherScannedCount)) return false;
        final Object thisSuccessCount = this.getSuccessCount();
        final Object otherSuccessCount = other.getSuccessCount();
        if (thisSuccessCount == null ? otherSuccessCount != null : !thisSuccessCount.equals(otherSuccessCount)) return false;
        final Object thisFailureCount = this.getFailureCount();
        final Object otherFailureCount = other.getFailureCount();
        if (thisFailureCount == null ? otherFailureCount != null : !thisFailureCount.equals(otherFailureCount)) return false;
        final Object thisSkippedCount = this.getSkippedCount();
        final Object otherSkippedCount = other.getSkippedCount();
        if (thisSkippedCount == null ? otherSkippedCount != null : !thisSkippedCount.equals(otherSkippedCount)) return false;
        final Object thisMode = this.getMode();
        final Object otherMode = other.getMode();
        if (thisMode == null ? otherMode != null : !thisMode.equals(otherMode)) return false;
        final Object thisSeasonKey = this.getSeasonKey();
        final Object otherSeasonKey = other.getSeasonKey();
        if (thisSeasonKey == null ? otherSeasonKey != null : !thisSeasonKey.equals(otherSeasonKey)) return false;
        final Object thisStartedAt = this.getStartedAt();
        final Object otherStartedAt = other.getStartedAt();
        if (thisStartedAt == null ? otherStartedAt != null : !thisStartedAt.equals(otherStartedAt)) return false;
        final Object thisCompletedAt = this.getCompletedAt();
        final Object otherCompletedAt = other.getCompletedAt();
        if (thisCompletedAt == null ? otherCompletedAt != null : !thisCompletedAt.equals(otherCompletedAt)) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        final Object thisErrorMessage = this.getErrorMessage();
        final Object otherErrorMessage = other.getErrorMessage();
        if (thisErrorMessage == null ? otherErrorMessage != null : !thisErrorMessage.equals(otherErrorMessage)) return false;
        final Object thisCheckpointJson = this.getCheckpointJson();
        final Object otherCheckpointJson = other.getCheckpointJson();
        if (thisCheckpointJson == null ? otherCheckpointJson != null : !thisCheckpointJson.equals(otherCheckpointJson)) return false;
        final Object thisSourceSnapshotAt = this.getSourceSnapshotAt();
        final Object otherSourceSnapshotAt = other.getSourceSnapshotAt();
        if (thisSourceSnapshotAt == null ? otherSourceSnapshotAt != null : !thisSourceSnapshotAt.equals(otherSourceSnapshotAt)) return false;
        final Object thisHeartbeatAt = this.getHeartbeatAt();
        final Object otherHeartbeatAt = other.getHeartbeatAt();
        if (thisHeartbeatAt == null ? otherHeartbeatAt != null : !thisHeartbeatAt.equals(otherHeartbeatAt)) return false;
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
        return other instanceof ImportRecord;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + this.getSubjectCount();
        final Object hashId = this.getId();
        result = result * PRIME + (hashId == null ? 43 : hashId.hashCode());
        final Object hashScannedCount = this.getScannedCount();
        result = result * PRIME + (hashScannedCount == null ? 43 : hashScannedCount.hashCode());
        final Object hashSuccessCount = this.getSuccessCount();
        result = result * PRIME + (hashSuccessCount == null ? 43 : hashSuccessCount.hashCode());
        final Object hashFailureCount = this.getFailureCount();
        result = result * PRIME + (hashFailureCount == null ? 43 : hashFailureCount.hashCode());
        final Object hashSkippedCount = this.getSkippedCount();
        result = result * PRIME + (hashSkippedCount == null ? 43 : hashSkippedCount.hashCode());
        final Object hashMode = this.getMode();
        result = result * PRIME + (hashMode == null ? 43 : hashMode.hashCode());
        final Object hashSeasonKey = this.getSeasonKey();
        result = result * PRIME + (hashSeasonKey == null ? 43 : hashSeasonKey.hashCode());
        final Object hashStartedAt = this.getStartedAt();
        result = result * PRIME + (hashStartedAt == null ? 43 : hashStartedAt.hashCode());
        final Object hashCompletedAt = this.getCompletedAt();
        result = result * PRIME + (hashCompletedAt == null ? 43 : hashCompletedAt.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        final Object hashErrorMessage = this.getErrorMessage();
        result = result * PRIME + (hashErrorMessage == null ? 43 : hashErrorMessage.hashCode());
        final Object hashCheckpointJson = this.getCheckpointJson();
        result = result * PRIME + (hashCheckpointJson == null ? 43 : hashCheckpointJson.hashCode());
        final Object hashSourceSnapshotAt = this.getSourceSnapshotAt();
        result = result * PRIME + (hashSourceSnapshotAt == null ? 43 : hashSourceSnapshotAt.hashCode());
        final Object hashHeartbeatAt = this.getHeartbeatAt();
        result = result * PRIME + (hashHeartbeatAt == null ? 43 : hashHeartbeatAt.hashCode());
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
        return "ImportRecord(id=" + this.getId() + ", mode=" + this.getMode() + ", seasonKey=" + this.getSeasonKey() + ", startedAt=" + this.getStartedAt() + ", completedAt=" + this.getCompletedAt() + ", status=" + this.getStatus() + ", subjectCount=" + this.getSubjectCount() + ", errorMessage=" + this.getErrorMessage() + ", checkpointJson=" + this.getCheckpointJson() + ", scannedCount=" + this.getScannedCount() + ", successCount=" + this.getSuccessCount() + ", failureCount=" + this.getFailureCount() + ", skippedCount=" + this.getSkippedCount() + ", sourceSnapshotAt=" + this.getSourceSnapshotAt() + ", heartbeatAt=" + this.getHeartbeatAt() + ", createdAt=" + this.getCreatedAt() + ")";
    }
}
