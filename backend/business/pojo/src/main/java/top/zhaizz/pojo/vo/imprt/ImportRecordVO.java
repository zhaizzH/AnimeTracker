package top.zhaizz.pojo.vo.imprt;

import java.time.LocalDateTime;

/**
 * 导入记录 VO
 */
public class ImportRecordVO {

    /** 记录ID */
    private Long id; // 记录ID
    /** 季度标识（如 2026-spring） */
    private String season; // 季度标识（如 2026-spring）
    /** 开始时间 */
    private LocalDateTime startedAt; // 开始时间
    /** 完成时间（可空） */
    private LocalDateTime completedAt; // 完成时间（可空）
    /** 状态: RUNNING, COMPLETED, FAILED */
    private String status; // 状态: RUNNING, COMPLETED, FAILED
    /** 本次导入的条目数 */
    private Integer subjectCount; // 本次导入的条目数
    /** 错误信息（失败时记录） */
    private String errorMessage; // 错误信息（失败时记录）

    /** 创建字段均为默认值的空导入记录 */
    public ImportRecordVO() {
    }

    /**
     * 获取记录ID
     * @return 导入记录主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取季度标识
     * @return 季度标识（如 2026-spring）；未提供时为 {@code null}
     */
    public String getSeason() {
        return this.season;
    }

    /**
     * 获取开始时间
     * @return 本次导入的开始时间；未提供时为 {@code null}
     */
    public LocalDateTime getStartedAt() {
        return this.startedAt;
    }

    /**
     * 获取完成时间
     * @return 本次导入的完成时间；任务未完成时为 {@code null}
     */
    public LocalDateTime getCompletedAt() {
        return this.completedAt;
    }

    /**
     * 获取状态
     * @return 任务状态：RUNNING、COMPLETED 或 FAILED；未提供时为 {@code null}
     */
    public String getStatus() {
        return this.status;
    }

    /**
     * 获取本次导入的条目数
     * @return 成功导入的条目数量；未提供时为 {@code null}
     */
    public Integer getSubjectCount() {
        return this.subjectCount;
    }

    /**
     * 获取错误信息
     * @return 失败时的错误描述；成功或进行中时为 {@code null}
     */
    public String getErrorMessage() {
        return this.errorMessage;
    }

    /**
     * 替换记录ID
     * @param id 导入记录主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换季度标识
     * @param season 季度标识（如 2026-spring），可为 {@code null}
     */
    public void setSeason(final String season) {
        this.season = season;
    }

    /**
     * 替换开始时间
     * @param startedAt 本次导入的开始时间，可为 {@code null}
     */
    public void setStartedAt(final LocalDateTime startedAt) {
        this.startedAt = startedAt;
    }

    /**
     * 替换完成时间
     * @param completedAt 本次导入的完成时间，可为 {@code null}
     */
    public void setCompletedAt(final LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }

    /**
     * 替换状态
     * @param status 任务状态：RUNNING、COMPLETED 或 FAILED，可为 {@code null}
     */
    public void setStatus(final String status) {
        this.status = status;
    }

    /**
     * 替换本次导入的条目数
     * @param subjectCount 成功导入的条目数量，可为 {@code null}
     */
    public void setSubjectCount(final Integer subjectCount) {
        this.subjectCount = subjectCount;
    }

    /**
     * 替换错误信息
     * @param errorMessage 失败时的错误描述，可为 {@code null}
     */
    public void setErrorMessage(final String errorMessage) {
        this.errorMessage = errorMessage;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ImportRecordVO)) return false;
        final ImportRecordVO other = (ImportRecordVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectCount = this.getSubjectCount();
        final Object otherSubjectCount = other.getSubjectCount();
        if (thisSubjectCount == null ? otherSubjectCount != null : !thisSubjectCount.equals(otherSubjectCount)) return false;
        final Object thisSeason = this.getSeason();
        final Object otherSeason = other.getSeason();
        if (thisSeason == null ? otherSeason != null : !thisSeason.equals(otherSeason)) return false;
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
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ImportRecordVO;
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
        final Object hashSubjectCount = this.getSubjectCount();
        result = result * PRIME + (hashSubjectCount == null ? 43 : hashSubjectCount.hashCode());
        final Object hashSeason = this.getSeason();
        result = result * PRIME + (hashSeason == null ? 43 : hashSeason.hashCode());
        final Object hashStartedAt = this.getStartedAt();
        result = result * PRIME + (hashStartedAt == null ? 43 : hashStartedAt.hashCode());
        final Object hashCompletedAt = this.getCompletedAt();
        result = result * PRIME + (hashCompletedAt == null ? 43 : hashCompletedAt.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        final Object hashErrorMessage = this.getErrorMessage();
        result = result * PRIME + (hashErrorMessage == null ? 43 : hashErrorMessage.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ImportRecordVO(id=" + this.getId() + ", season=" + this.getSeason() + ", startedAt=" + this.getStartedAt() + ", completedAt=" + this.getCompletedAt() + ", status=" + this.getStatus() + ", subjectCount=" + this.getSubjectCount() + ", errorMessage=" + this.getErrorMessage() + ")";
    }
}
