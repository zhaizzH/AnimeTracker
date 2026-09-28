package top.zhaizz.pojo.vo.log;

import java.util.List;

/**
 * 日志分页结果
 */
public class LogVO {

    /** 当前页日志明细 */
    private List<OperationLogVO> content; // 当前页日志明细
    /** 匹配筛选条件的日志总数(分页) */
    private long total; // 匹配筛选条件的日志总数(分页)
    /** 当前页码 */
    private int page; // 当前页码
    /** 每页条数 */
    private int size; // 每页条数
    /** 当前筛选条件下全量聚合统计 */
    private OperationLogStatsVO stats; // 当前筛选条件下全量聚合统计

    /** 创建字段均为默认值的空分页结果 */
    public LogVO() {
    }

    /**
     * 获取当前页日志明细
     * @return 当前页的操作日志列表；未提供时为 {@code null}
     */
    public List<OperationLogVO> getContent() {
        return this.content;
    }

    /**
     * 获取匹配筛选条件的日志总数
     * @return 满足筛选条件的日志总数，未设置时为 {@code 0}
     */
    public long getTotal() {
        return this.total;
    }

    /**
     * 获取当前页码
     * @return 当前页码（从 1 开始），未设置时为 {@code 0}
     */
    public int getPage() {
        return this.page;
    }

    /**
     * 获取每页条数
     * @return 每页返回的日志条数，未设置时为 {@code 0}
     */
    public int getSize() {
        return this.size;
    }

    /**
     * 获取全量聚合统计
     * @return 当前筛选条件下的全量聚合统计；未提供时为 {@code null}
     */
    public OperationLogStatsVO getStats() {
        return this.stats;
    }

    /**
     * 替换当前页日志明细
     * @param content 当前页的操作日志列表，可为 {@code null}
     */
    public void setContent(final List<OperationLogVO> content) {
        this.content = content;
    }

    /**
     * 替换匹配筛选条件的日志总数
     * @param total 满足筛选条件的日志总数
     */
    public void setTotal(final long total) {
        this.total = total;
    }

    /**
     * 替换当前页码
     * @param page 当前页码（从 1 开始）
     */
    public void setPage(final int page) {
        this.page = page;
    }

    /**
     * 替换每页条数
     * @param size 每页返回的日志条数
     */
    public void setSize(final int size) {
        this.size = size;
    }

    /**
     * 替换全量聚合统计
     * @param stats 当前筛选条件下的全量聚合统计，可为 {@code null}
     */
    public void setStats(final OperationLogStatsVO stats) {
        this.stats = stats;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LogVO)) return false;
        final LogVO other = (LogVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getTotal() != other.getTotal()) return false;
        if (this.getPage() != other.getPage()) return false;
        if (this.getSize() != other.getSize()) return false;
        final Object thisContent = this.getContent();
        final Object otherContent = other.getContent();
        if (thisContent == null ? otherContent != null : !thisContent.equals(otherContent)) return false;
        final Object thisStats = this.getStats();
        final Object otherStats = other.getStats();
        if (thisStats == null ? otherStats != null : !thisStats.equals(otherStats)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof LogVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashTotal = this.getTotal();
        result = result * PRIME + (int) (hashTotal >>> 32 ^ hashTotal);
        result = result * PRIME + this.getPage();
        result = result * PRIME + this.getSize();
        final Object hashContent = this.getContent();
        result = result * PRIME + (hashContent == null ? 43 : hashContent.hashCode());
        final Object hashStats = this.getStats();
        result = result * PRIME + (hashStats == null ? 43 : hashStats.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "LogVO(content=" + this.getContent() + ", total=" + this.getTotal() + ", page=" + this.getPage() + ", size=" + this.getSize() + ", stats=" + this.getStats() + ")";
    }
}
