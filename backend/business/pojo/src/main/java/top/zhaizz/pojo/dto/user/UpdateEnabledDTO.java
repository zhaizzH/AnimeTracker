package top.zhaizz.pojo.dto.user;

import jakarta.validation.constraints.NotNull;

/**
 * UpdateEnabledDTO 数据对象
 */
public class UpdateEnabledDTO {
    /**
     * 用户或资源是否处于启用状态
     */
    @NotNull(message = "启用状态不能为空")
    private Boolean enabled;

    /** 创建启用状态待填充的空请求对象 */
    public UpdateEnabledDTO() {
    }

    /**
     * 获取启用状态
     * @return 用户或资源是否启用；为 {@code null} 时校验失败
     */
    public Boolean getEnabled() {
        return this.enabled;
    }

    /**
     * 替换启用状态
     * @param enabled 用户或资源是否启用；不可为 {@code null}
     */
    public void setEnabled(final Boolean enabled) {
        this.enabled = enabled;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof UpdateEnabledDTO)) return false;
        final UpdateEnabledDTO other = (UpdateEnabledDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisEnabled = this.getEnabled();
        final Object otherEnabled = other.getEnabled();
        if (thisEnabled == null ? otherEnabled != null : !thisEnabled.equals(otherEnabled)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof UpdateEnabledDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashEnabled = this.getEnabled();
        result = result * PRIME + (hashEnabled == null ? 43 : hashEnabled.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "UpdateEnabledDTO(enabled=" + this.getEnabled() + ")";
    }
}
