package top.zhaizz.pojo.vo.log;

/**
 * 操作日志统计（按当前筛选条件对全部日志聚合）
 */
public class OperationLogStatsVO {

    /** 日志总数 */
    private Long total; // 日志总数
    /** 失败日志数 */
    private Long failedCount; // 失败日志数
    /** 成功日志数 */
    private Long successCount; // 成功日志数
    /** 平均耗时(毫秒) */
    private Long avgDurationMs; // 平均耗时(毫秒)

    /** 创建字段均为默认值的空统计对象 */
    public OperationLogStatsVO() {
    }

    /**
     * 获取日志总数
     * @return 当前筛选条件下的日志总数；未提供时为 {@code null}
     */
    public Long getTotal() {
        return this.total;
    }

    /**
     * 获取失败日志数
     * @return 状态为失败的日志数量；未提供时为 {@code null}
     */
    public Long getFailedCount() {
        return this.failedCount;
    }

    /**
     * 获取成功日志数
     * @return 状态为成功的日志数量；未提供时为 {@code null}
     */
    public Long getSuccessCount() {
        return this.successCount;
    }

    /**
     * 获取平均耗时
     * @return 日志的平均耗时（毫秒）；未提供时为 {@code null}
     */
    public Long getAvgDurationMs() {
        return this.avgDurationMs;
    }

    /**
     * 替换日志总数
     * @param total 当前筛选条件下的日志总数，可为 {@code null}
     */
    public void setTotal(final Long total) {
        this.total = total;
    }

    /**
     * 替换失败日志数
     * @param failedCount 状态为失败的日志数量，可为 {@code null}
     */
    public void setFailedCount(final Long failedCount) {
        this.failedCount = failedCount;
    }

    /**
     * 替换成功日志数
     * @param successCount 状态为成功的日志数量，可为 {@code null}
     */
    public void setSuccessCount(final Long successCount) {
        this.successCount = successCount;
    }

    /**
     * 替换平均耗时
     * @param avgDurationMs 日志的平均耗时（毫秒），可为 {@code null}
     */
    public void setAvgDurationMs(final Long avgDurationMs) {
        this.avgDurationMs = avgDurationMs;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof OperationLogStatsVO)) return false;
        final OperationLogStatsVO other = (OperationLogStatsVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisTotal = this.getTotal();
        final Object otherTotal = other.getTotal();
        if (thisTotal == null ? otherTotal != null : !thisTotal.equals(otherTotal)) return false;
        final Object thisFailedCount = this.getFailedCount();
        final Object otherFailedCount = other.getFailedCount();
        if (thisFailedCount == null ? otherFailedCount != null : !thisFailedCount.equals(otherFailedCount)) return false;
        final Object thisSuccessCount = this.getSuccessCount();
        final Object otherSuccessCount = other.getSuccessCount();
        if (thisSuccessCount == null ? otherSuccessCount != null : !thisSuccessCount.equals(otherSuccessCount)) return false;
        final Object thisAvgDurationMs = this.getAvgDurationMs();
        final Object otherAvgDurationMs = other.getAvgDurationMs();
        if (thisAvgDurationMs == null ? otherAvgDurationMs != null : !thisAvgDurationMs.equals(otherAvgDurationMs)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof OperationLogStatsVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashTotal = this.getTotal();
        result = result * PRIME + (hashTotal == null ? 43 : hashTotal.hashCode());
        final Object hashFailedCount = this.getFailedCount();
        result = result * PRIME + (hashFailedCount == null ? 43 : hashFailedCount.hashCode());
        final Object hashSuccessCount = this.getSuccessCount();
        result = result * PRIME + (hashSuccessCount == null ? 43 : hashSuccessCount.hashCode());
        final Object hashAvgDurationMs = this.getAvgDurationMs();
        result = result * PRIME + (hashAvgDurationMs == null ? 43 : hashAvgDurationMs.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "OperationLogStatsVO(total=" + this.getTotal() + ", failedCount=" + this.getFailedCount() + ", successCount=" + this.getSuccessCount() + ", avgDurationMs=" + this.getAvgDurationMs() + ")";
    }
}
