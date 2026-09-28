package top.zhaizz.pojo.vo.imprt;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 导入状态信息 VO
 */
public class ImportStatusVO {

    /** 最近一次导入完成时间（从未导入=null） */
    private LocalDateTime lastImportedAt; // 最近一次导入完成时间（从未导入=null）
    /** 当前导入日志数量（import_record 全量） */
    private Long totalLogs; // 当前导入日志数量（import_record 全量）
    /** 历史成功任务总数（全量） */
    private Long completedCount; // 历史成功任务总数（全量）
    /** 历史失败任务总数（全量） */
    private Long failedCount; // 历史失败任务总数（全量）
    /** 最近条目导入记录 */
    private List<ImportRecordVO> recentRecords; // 最近条目导入记录

    /** 创建字段均为默认值的空状态对象 */
    public ImportStatusVO() {
    }

    /**
     * 获取最近一次导入完成时间
     * @return 最近一次成功导入的完成时间；从未导入时为 {@code null}
     */
    public LocalDateTime getLastImportedAt() {
        return this.lastImportedAt;
    }

    /**
     * 获取当前导入日志数量
     * @return import_record 全量记录数；未提供时为 {@code null}
     */
    public Long getTotalLogs() {
        return this.totalLogs;
    }

    /**
     * 获取历史成功任务总数
     * @return 全量成功导入任务数；未提供时为 {@code null}
     */
    public Long getCompletedCount() {
        return this.completedCount;
    }

    /**
     * 获取历史失败任务总数
     * @return 全量失败导入任务数；未提供时为 {@code null}
     */
    public Long getFailedCount() {
        return this.failedCount;
    }

    /**
     * 获取最近条目导入记录
     * @return 最近的导入记录列表；未提供时为 {@code null}
     */
    public List<ImportRecordVO> getRecentRecords() {
        return this.recentRecords;
    }

    /**
     * 替换最近一次导入完成时间
     * @param lastImportedAt 最近一次成功导入的完成时间，可为 {@code null}
     */
    public void setLastImportedAt(final LocalDateTime lastImportedAt) {
        this.lastImportedAt = lastImportedAt;
    }

    /**
     * 替换当前导入日志数量
     * @param totalLogs import_record 全量记录数，可为 {@code null}
     */
    public void setTotalLogs(final Long totalLogs) {
        this.totalLogs = totalLogs;
    }

    /**
     * 替换历史成功任务总数
     * @param completedCount 全量成功导入任务数，可为 {@code null}
     */
    public void setCompletedCount(final Long completedCount) {
        this.completedCount = completedCount;
    }

    /**
     * 替换历史失败任务总数
     * @param failedCount 全量失败导入任务数，可为 {@code null}
     */
    public void setFailedCount(final Long failedCount) {
        this.failedCount = failedCount;
    }

    /**
     * 替换最近条目导入记录
     * @param recentRecords 最近的导入记录列表，可为 {@code null}
     */
    public void setRecentRecords(final List<ImportRecordVO> recentRecords) {
        this.recentRecords = recentRecords;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ImportStatusVO)) return false;
        final ImportStatusVO other = (ImportStatusVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisTotalLogs = this.getTotalLogs();
        final Object otherTotalLogs = other.getTotalLogs();
        if (thisTotalLogs == null ? otherTotalLogs != null : !thisTotalLogs.equals(otherTotalLogs)) return false;
        final Object thisCompletedCount = this.getCompletedCount();
        final Object otherCompletedCount = other.getCompletedCount();
        if (thisCompletedCount == null ? otherCompletedCount != null : !thisCompletedCount.equals(otherCompletedCount)) return false;
        final Object thisFailedCount = this.getFailedCount();
        final Object otherFailedCount = other.getFailedCount();
        if (thisFailedCount == null ? otherFailedCount != null : !thisFailedCount.equals(otherFailedCount)) return false;
        final Object thisLastImportedAt = this.getLastImportedAt();
        final Object otherLastImportedAt = other.getLastImportedAt();
        if (thisLastImportedAt == null ? otherLastImportedAt != null : !thisLastImportedAt.equals(otherLastImportedAt)) return false;
        final Object thisRecentRecords = this.getRecentRecords();
        final Object otherRecentRecords = other.getRecentRecords();
        if (thisRecentRecords == null ? otherRecentRecords != null : !thisRecentRecords.equals(otherRecentRecords)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ImportStatusVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashTotalLogs = this.getTotalLogs();
        result = result * PRIME + (hashTotalLogs == null ? 43 : hashTotalLogs.hashCode());
        final Object hashCompletedCount = this.getCompletedCount();
        result = result * PRIME + (hashCompletedCount == null ? 43 : hashCompletedCount.hashCode());
        final Object hashFailedCount = this.getFailedCount();
        result = result * PRIME + (hashFailedCount == null ? 43 : hashFailedCount.hashCode());
        final Object hashLastImportedAt = this.getLastImportedAt();
        result = result * PRIME + (hashLastImportedAt == null ? 43 : hashLastImportedAt.hashCode());
        final Object hashRecentRecords = this.getRecentRecords();
        result = result * PRIME + (hashRecentRecords == null ? 43 : hashRecentRecords.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ImportStatusVO(lastImportedAt=" + this.getLastImportedAt() + ", totalLogs=" + this.getTotalLogs() + ", completedCount=" + this.getCompletedCount() + ", failedCount=" + this.getFailedCount() + ", recentRecords=" + this.getRecentRecords() + ")";
    }
}
