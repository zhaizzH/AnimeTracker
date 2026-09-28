package top.zhaizz.pojo.vo.subject;

/**
 * 导入状态分布
 */
public class SubjectStatusCountVO {
    /** 导入状态: 0=待导入, 1=已导入 */
    private Integer importStatus;   // 导入状态: 0=待导入, 1=已导入
    /** 该状态条目数 */
    private long count;             // 该状态条目数

    /** 创建字段均为默认值的空状态分布 */
    public SubjectStatusCountVO() {
    }

    /**
     * 获取导入状态
     * @return 导入状态编码；0=待导入, 1=已导入，未提供时为 {@code null}
     */
    public Integer getImportStatus() {
        return this.importStatus;
    }

    /**
     * 获取该状态条目数
     * @return 处于该导入状态的条目数量，未设置时默认为 {@code 0}
     */
    public long getCount() {
        return this.count;
    }

    /**
     * 替换导入状态
     * @param importStatus 导入状态编码；0=待导入, 1=已导入，可为 {@code null}
     */
    public void setImportStatus(final Integer importStatus) {
        this.importStatus = importStatus;
    }

    /**
     * 替换该状态条目数
     * @param count 处于该导入状态的条目数量，取值为基本类型 long
     */
    public void setCount(final long count) {
        this.count = count;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectStatusCountVO)) return false;
        final SubjectStatusCountVO other = (SubjectStatusCountVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getCount() != other.getCount()) return false;
        final Object thisImportStatus = this.getImportStatus();
        final Object otherImportStatus = other.getImportStatus();
        if (thisImportStatus == null ? otherImportStatus != null : !thisImportStatus.equals(otherImportStatus)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectStatusCountVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashCount = this.getCount();
        result = result * PRIME + (int) (hashCount >>> 32 ^ hashCount);
        final Object hashImportStatus = this.getImportStatus();
        result = result * PRIME + (hashImportStatus == null ? 43 : hashImportStatus.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectStatusCountVO(importStatus=" + this.getImportStatus() + ", count=" + this.getCount() + ")";
    }
}
