package top.zhaizz.pojo.dto.collection;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/**
 * 收藏列表查询参数
 */
public class CollectionQueryDTO {
    /**
     * 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
     */
    @Min(value = 1, message = "收藏类型范围 1-5")
    @Max(value = 5, message = "收藏类型范围 1-5")
    private Integer type; // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
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

    /** 创建使用默认页码与每页条数的空查询对象 */
    public CollectionQueryDTO() {
    }

    /**
     * 获取收藏类型
     * @return 收藏类型筛选值，1=想看、2=看过、3=在看、4=搁置、5=抛弃；为 {@code null} 时不过滤类型
     */
    public Integer getType() {
        return this.type;
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
     * 替换收藏类型
     * @param type 收藏类型筛选值，1=想看、2=看过、3=在看、4=搁置、5=抛弃；可为 {@code null} 表示不过滤
     */
    public void setType(final Integer type) {
        this.type = type;
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
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionQueryDTO)) return false;
        final CollectionQueryDTO other = (CollectionQueryDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getPage() != other.getPage()) return false;
        if (this.getSize() != other.getSize()) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CollectionQueryDTO;
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
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CollectionQueryDTO(type=" + this.getType() + ", page=" + this.getPage() + ", size=" + this.getSize() + ")";
    }
}
