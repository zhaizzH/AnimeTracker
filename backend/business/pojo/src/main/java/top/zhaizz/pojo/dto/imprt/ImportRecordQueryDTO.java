package top.zhaizz.pojo.dto.imprt;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/**
 * 导入记录分页查询参数
 */
public class ImportRecordQueryDTO {
    /**
     * 页码
     */
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1; // 页码
    /**
     * 每页条数（导入记录量大，默认 10 上限 1000）
     */
    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 1000, message = "每页条数不能超过1000")
    private int size = 10; // 每页条数（导入记录量大，默认 10 上限 1000）
    /**
     * 状态过滤：RUNNING / COMPLETED / FAILED，空表示全部
     */
    private String status; // 状态过滤：RUNNING / COMPLETED / FAILED，空表示全部

    /** 创建使用默认分页参数的空查询对象 */
    public ImportRecordQueryDTO() {
    }

    /**
     * 获取页码
     * @return 当前页码，默认 1，取值不得小于 1
     */
    public int getPage() {
        return this.page;
    }

    /**
     * 获取每页条数
     * @return 单页记录数，默认 10，取值需在 1~1000 之间
     */
    public int getSize() {
        return this.size;
    }

    /**
     * 获取状态过滤条件
     * @return 导入状态过滤值 RUNNING / COMPLETED / FAILED；为 {@code null} 或空串时不过滤状态
     */
    public String getStatus() {
        return this.status;
    }

    /**
     * 替换页码
     * @param page 新的页码，从 1 开始，不得小于 1
     */
    public void setPage(final int page) {
        this.page = page;
    }

    /**
     * 替换每页条数
     * @param size 新的单页记录数，需在 1~1000 之间
     */
    public void setSize(final int size) {
        this.size = size;
    }

    /**
     * 替换状态过滤条件
     * @param status 导入状态过滤值 RUNNING / COMPLETED / FAILED；可为 {@code null} 或空串表示不过滤
     */
    public void setStatus(final String status) {
        this.status = status;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ImportRecordQueryDTO)) return false;
        final ImportRecordQueryDTO other = (ImportRecordQueryDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getPage() != other.getPage()) return false;
        if (this.getSize() != other.getSize()) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ImportRecordQueryDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + this.getPage();
        result = result * PRIME + this.getSize();
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ImportRecordQueryDTO(page=" + this.getPage() + ", size=" + this.getSize() + ", status=" + this.getStatus() + ")";
    }
}
