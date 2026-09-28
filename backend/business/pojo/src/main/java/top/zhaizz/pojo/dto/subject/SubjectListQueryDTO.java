package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/**
 * 番剧列表查询参数（排序字段进 SQL 走白名单，无注入风险）
 */
public class SubjectListQueryDTO {
    /**
     * 页码
     */
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1; // 页码
    /**
     * 每页条数
     */
    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20; // 每页条数
    /**
     * 排序字段（score/rank/collection_total/...）
     */
    private String sort = "score"; // 排序字段（score/rank/collection_total/...）
    /**
     * 排序方向（asc/desc）
     */
    private String order = "desc"; // 排序方向（asc/desc）

    /** 创建使用默认排序与分页参数的空查询对象 */
    public SubjectListQueryDTO() {
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
     * @return 单页记录数，默认 20，取值需在 1~100 之间
     */
    public int getSize() {
        return this.size;
    }

    /**
     * 获取排序字段
     * @return 排序字段名，默认 score；取值会经白名单校验后再拼入 SQL
     */
    public String getSort() {
        return this.sort;
    }

    /**
     * 获取排序方向
     * @return 排序方向 asc 或 desc，默认 desc
     */
    public String getOrder() {
        return this.order;
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
     * @param size 新的单页记录数，需在 1~100 之间
     */
    public void setSize(final int size) {
        this.size = size;
    }

    /**
     * 替换排序字段
     * @param sort 排序字段名，例如 score、rank、collection_total；非白名单取值会被拒绝
     */
    public void setSort(final String sort) {
        this.sort = sort;
    }

    /**
     * 替换排序方向
     * @param order 排序方向 asc 或 desc
     */
    public void setOrder(final String order) {
        this.order = order;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectListQueryDTO)) return false;
        final SubjectListQueryDTO other = (SubjectListQueryDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getPage() != other.getPage()) return false;
        if (this.getSize() != other.getSize()) return false;
        final Object thisSort = this.getSort();
        final Object otherSort = other.getSort();
        if (thisSort == null ? otherSort != null : !thisSort.equals(otherSort)) return false;
        final Object thisOrder = this.getOrder();
        final Object otherOrder = other.getOrder();
        if (thisOrder == null ? otherOrder != null : !thisOrder.equals(otherOrder)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectListQueryDTO;
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
        final Object hashSort = this.getSort();
        result = result * PRIME + (hashSort == null ? 43 : hashSort.hashCode());
        final Object hashOrder = this.getOrder();
        result = result * PRIME + (hashOrder == null ? 43 : hashOrder.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectListQueryDTO(page=" + this.getPage() + ", size=" + this.getSize() + ", sort=" + this.getSort() + ", order=" + this.getOrder() + ")";
    }
}
