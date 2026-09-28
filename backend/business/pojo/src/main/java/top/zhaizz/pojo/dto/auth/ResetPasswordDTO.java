package top.zhaizz.pojo.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 忘记密码 — 重置密码请求 DTO
 */
public class ResetPasswordDTO {
    /**
     * 邮箱
     */
    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email; // 邮箱
    /**
     * 验证码（6位）
     */
    @NotBlank(message = "验证码不能为空")
    @Size(min = 6, max = 6, message = "验证码为6位")
    private String code; // 验证码（6位）
    /**
     * 新密码
     */
    @NotBlank(message = "新密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度需在6~128之间")
    private String newPassword; // 新密码

    /** 创建字段均为默认值的空请求对象 */
    public ResetPasswordDTO() {
    }

    /**
     * 获取邮箱
     * @return 接收重置验证码的邮箱；未提供时为 {@code null}，必填且需通过邮箱格式校验
     */
    public String getEmail() {
        return this.email;
    }

    /**
     * 获取验证码
     * @return 发往该邮箱的 6 位重置验证码；未提供时为 {@code null}，必填且长度必须恰好为 6
     */
    public String getCode() {
        return this.code;
    }

    /**
     * 获取新密码
     * @return 待设置的新密码；未提供时为 {@code null}，必填且长度需在 6~128 之间
     */
    public String getNewPassword() {
        return this.newPassword;
    }

    /**
     * 替换邮箱
     * @param email 接收重置验证码的邮箱；可为 {@code null}，非空时需通过邮箱格式校验
     */
    public void setEmail(final String email) {
        this.email = email;
    }

    /**
     * 替换验证码
     * @param code 发往该邮箱的 6 位重置验证码；可为 {@code null}，非空时长度必须恰好为 6
     */
    public void setCode(final String code) {
        this.code = code;
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
        if (!(o instanceof ResetPasswordDTO)) return false;
        final ResetPasswordDTO other = (ResetPasswordDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisEmail = this.getEmail();
        final Object otherEmail = other.getEmail();
        if (thisEmail == null ? otherEmail != null : !thisEmail.equals(otherEmail)) return false;
        final Object thisCode = this.getCode();
        final Object otherCode = other.getCode();
        if (thisCode == null ? otherCode != null : !thisCode.equals(otherCode)) return false;
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
        return other instanceof ResetPasswordDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashEmail = this.getEmail();
        result = result * PRIME + (hashEmail == null ? 43 : hashEmail.hashCode());
        final Object hashCode = this.getCode();
        result = result * PRIME + (hashCode == null ? 43 : hashCode.hashCode());
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
        return "ResetPasswordDTO(email=" + this.getEmail() + ", code=" + this.getCode() + ", newPassword=" + this.getNewPassword() + ")";
    }
}
