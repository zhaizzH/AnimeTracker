package top.zhaizz.pojo.dto.collection;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

/**
 * 追番收藏更新请求 DTO
 */
public class CollectionUpdateDTO {
    /**
     * 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
     */
    @NotNull(message = "收藏类型不能为空")
    @Min(value = 1, message = "收藏类型范围 1-5")
    @Max(value = 5, message = "收藏类型范围 1-5")
    private Integer type; // 收藏状态: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    /**
     * 评分（0~10, 0 表示未评分）
     */
    @Min(value = 0, message = "评分范围 0-10")
    @Max(value = 10, message = "评分范围 0-10")
    private Integer rate; // 评分（0~10, 0 表示未评分）
    /**
     * 看到第几集
     */
    @Min(value = 0, message = "剧集进度不能为负")
    private Integer epStatus; // 看到第几集

    /** 创建待填充更新字段的空请求对象 */
    public CollectionUpdateDTO() {
    }

    /**
     * 获取收藏状态
     * @return 收藏状态值，1=想看、2=看过、3=在看、4=搁置、5=抛弃；为 {@code null} 时校验失败
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取评分
     * @return 评分 0~10，其中 0 表示未评分；为 {@code null} 时表示不更新评分
     */
    public Integer getRate() {
        return this.rate;
    }

    /**
     * 获取剧集进度
     * @return 已观看到第几集，不得为负；为 {@code null} 时表示不更新进度
     */
    public Integer getEpStatus() {
        return this.epStatus;
    }

    /**
     * 替换收藏状态
     * @param type 收藏状态值，1=想看、2=看过、3=在看、4=搁置、5=抛弃；不可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换评分
     * @param rate 评分 0~10，其中 0 表示未评分；可为 {@code null} 表示不更新评分
     */
    public void setRate(final Integer rate) {
        this.rate = rate;
    }

    /**
     * 替换剧集进度
     * @param epStatus 已观看到第几集，不得为负；可为 {@code null} 表示不更新进度
     */
    public void setEpStatus(final Integer epStatus) {
        this.epStatus = epStatus;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionUpdateDTO)) return false;
        final CollectionUpdateDTO other = (CollectionUpdateDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisRate = this.getRate();
        final Object otherRate = other.getRate();
        if (thisRate == null ? otherRate != null : !thisRate.equals(otherRate)) return false;
        final Object thisEpStatus = this.getEpStatus();
        final Object otherEpStatus = other.getEpStatus();
        if (thisEpStatus == null ? otherEpStatus != null : !thisEpStatus.equals(otherEpStatus)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CollectionUpdateDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashRate = this.getRate();
        result = result * PRIME + (hashRate == null ? 43 : hashRate.hashCode());
        final Object hashEpStatus = this.getEpStatus();
        result = result * PRIME + (hashEpStatus == null ? 43 : hashEpStatus.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CollectionUpdateDTO(type=" + this.getType() + ", rate=" + this.getRate() + ", epStatus=" + this.getEpStatus() + ")";
    }
}
