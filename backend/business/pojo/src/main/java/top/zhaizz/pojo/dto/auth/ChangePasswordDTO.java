package top.zhaizz.pojo.dto.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 修改密码请求 DTO
 */
public class ChangePasswordDTO {
    /**
     * 旧密码
     */
    @NotBlank(message = "旧密码不能为空")
    private String oldPassword; // 旧密码
    /**
     * 新密码
     */
    @NotBlank(message = "新密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度需在6~128之间")
    private String newPassword; // 新密码

    /** 创建字段均为默认值的空请求对象 */
    public ChangePasswordDTO() {
    }

    /**
     * 获取旧密码
     * @return 当前账户的旧密码；未提供时为 {@code null}，必填且用于身份校验
     */
    public String getOldPassword() {
        return this.oldPassword;
    }

    /**
     * 获取新密码
     * @return 待设置的新密码；未提供时为 {@code null}，必填且长度需在 6~128 之间
     */
    public String getNewPassword() {
        return this.newPassword;
    }

    /**
     * 替换旧密码
     * @param oldPassword 当前账户的旧密码；可为 {@code null}，但校验要求其非空
     */
    public void setOldPassword(final String oldPassword) {
        this.oldPassword = oldPassword;
    }

    /**
     * 替换新密码
     * @param newPassword 待设置的新密码；可为 {@code null}，非空时长度需在 6~128 之间
     */
    public void setNewPassword(final String newPassword) {
        this.newPassword = newPassword;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ChangePasswordDTO)) return false;
        final ChangePasswordDTO other = (ChangePasswordDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisOldPassword = this.getOldPassword();
        final Object otherOldPassword = other.getOldPassword();
        if (thisOldPassword == null ? otherOldPassword != null : !thisOldPassword.equals(otherOldPassword)) return false;
        final Object thisNewPassword = this.getNewPassword();
        final Object otherNewPassword = other.getNewPassword();
        if (thisNewPassword == null ? otherNewPassword != null : !thisNewPassword.equals(otherNewPassword)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ChangePasswordDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashOldPassword = this.getOldPassword();
        result = result * PRIME + (hashOldPassword == null ? 43 : hashOldPassword.hashCode());
        final Object hashNewPassword = this.getNewPassword();
        result = result * PRIME + (hashNewPassword == null ? 43 : hashNewPassword.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ChangePasswordDTO(oldPassword=" + this.getOldPassword() + ", newPassword=" + this.getNewPassword() + ")";
    }
}
