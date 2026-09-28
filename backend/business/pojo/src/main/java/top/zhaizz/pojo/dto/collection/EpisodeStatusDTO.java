package top.zhaizz.pojo.dto.collection;

import jakarta.validation.constraints.Min;

/**
 * 剧集进度更新请求 DTO
 */
public class EpisodeStatusDTO {
    /**
     * 看到第几集
     */
    @Min(value = 0, message = "剧集进度不能为负")
    private int epStatus; // 看到第几集

    /** 创建进度默认为 0 的空请求对象 */
    public EpisodeStatusDTO() {
    }

    /**
     * 获取剧集进度
     * @return 已观看到第几集，默认 0 表示尚未观看，不得为负
     */
    public int getEpStatus() {
        return this.epStatus;
    }

    /**
     * 替换剧集进度
     * @param epStatus 已观看到第几集，不得为负
     */
    public void setEpStatus(final int epStatus) {
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
        if (!(o instanceof EpisodeStatusDTO)) return false;
        final EpisodeStatusDTO other = (EpisodeStatusDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getEpStatus() != other.getEpStatus()) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof EpisodeStatusDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + this.getEpStatus();
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "EpisodeStatusDTO(epStatus=" + this.getEpStatus() + ")";
    }
}
