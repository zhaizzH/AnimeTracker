package top.zhaizz.pojo.vo.imprt;

/**
 * 导入记录统计
 */
public class ImportStatVO {

    /** 导入总次数 */
    private long importTotal; // 导入总次数
    /** 成功次数 */
    private long importSucceeded; // 成功次数
    /** 失败次数 */
    private long importFailed; // 失败次数

    /** 创建各项计数均为零的空统计对象 */
    public ImportStatVO() {
    }

    /**
     * 获取导入总次数
     * @return 导入任务总次数，未设置时为 {@code 0}
     */
    public long getImportTotal() {
        return this.importTotal;
    }

    /**
     * 获取成功次数
     * @return 导入成功的次数，未设置时为 {@code 0}
     */
    public long getImportSucceeded() {
        return this.importSucceeded;
    }

    /**
     * 获取失败次数
     * @return 导入失败的次数，未设置时为 {@code 0}
     */
    public long getImportFailed() {
        return this.importFailed;
    }

    /**
     * 替换导入总次数
     * @param importTotal 导入任务总次数
     */
    public void setImportTotal(final long importTotal) {
        this.importTotal = importTotal;
    }

    /**
     * 替换成功次数
     * @param importSucceeded 导入成功的次数
     */
    public void setImportSucceeded(final long importSucceeded) {
        this.importSucceeded = importSucceeded;
    }

    /**
     * 替换失败次数
     * @param importFailed 导入失败的次数
     */
    public void setImportFailed(final long importFailed) {
        this.importFailed = importFailed;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ImportStatVO)) return false;
        final ImportStatVO other = (ImportStatVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getImportTotal() != other.getImportTotal()) return false;
        if (this.getImportSucceeded() != other.getImportSucceeded()) return false;
        if (this.getImportFailed() != other.getImportFailed()) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ImportStatVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashImportTotal = this.getImportTotal();
        result = result * PRIME + (int) (hashImportTotal >>> 32 ^ hashImportTotal);
        final long hashImportSucceeded = this.getImportSucceeded();
        result = result * PRIME + (int) (hashImportSucceeded >>> 32 ^ hashImportSucceeded);
        final long hashImportFailed = this.getImportFailed();
        result = result * PRIME + (int) (hashImportFailed >>> 32 ^ hashImportFailed);
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ImportStatVO(importTotal=" + this.getImportTotal() + ", importSucceeded=" + this.getImportSucceeded() + ", importFailed=" + this.getImportFailed() + ")";
    }
}
