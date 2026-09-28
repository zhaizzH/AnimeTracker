package top.zhaizz.pojo.dto.user;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * 修改角色请求 DTO
 */
public class UpdateRoleDTO {
    /**
     * 角色: USER=普通用户, ADMIN=管理员
     */
    @NotBlank(message = "角色不能为空")
    @Pattern(regexp = "USER|ADMIN", message = "角色值必须是 USER 或 ADMIN")
    private String role; // 角色: USER=普通用户, ADMIN=管理员

    /** 创建角色待填充的空请求对象 */
    public UpdateRoleDTO() {
    }

    /**
     * 获取角色
     * @return 角色标识 USER 或 ADMIN；未提供时为 {@code null}，必填且取值受枚举约束
     */
    public String getRole() {
        return this.role;
    }

    /**
     * 替换角色
     * @param role 角色标识 USER 或 ADMIN；可为 {@code null}，但校验要求其非空且取值合法
     */
    public void setRole(final String role) {
        this.role = role;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof UpdateRoleDTO)) return false;
        final UpdateRoleDTO other = (UpdateRoleDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisRole = this.getRole();
        final Object otherRole = other.getRole();
        if (thisRole == null ? otherRole != null : !thisRole.equals(otherRole)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof UpdateRoleDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashRole = this.getRole();
        result = result * PRIME + (hashRole == null ? 43 : hashRole.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "UpdateRoleDTO(role=" + this.getRole() + ")";
    }
}
