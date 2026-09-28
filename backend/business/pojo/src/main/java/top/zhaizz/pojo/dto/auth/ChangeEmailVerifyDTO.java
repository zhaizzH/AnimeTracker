package top.zhaizz.pojo.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 校验邮箱修改验证码请求 DTO（通过后更新绑定邮箱）
 */
public class ChangeEmailVerifyDTO {
    /**
     * 新邮箱
     */
    @NotBlank(message = "新邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    @Size(max = 128, message = "邮箱长度不能超过128")
    private String newEmail; // 新邮箱
    /**
     * 验证码（6位）
     */
    @NotBlank(message = "验证码不能为空")
    @Size(min = 6, max = 6, message = "验证码为6位")
    private String code; // 验证码（6位）

    /** 创建字段均为默认值的空请求对象 */
    public ChangeEmailVerifyDTO() {
    }

    /**
     * 获取新邮箱
     * @return 待改绑的新邮箱；未提供时为 {@code null}，必填且需通过邮箱格式校验，最长 128 字符
     */
    public String getNewEmail() {
        return this.newEmail;
    }

    /**
     * 获取验证码
     * @return 发往新邮箱的 6 位验证码；未提供时为 {@code null}，必填且长度必须恰好为 6
     */
    public String getCode() {
        return this.code;
    }

    /**
     * 替换新邮箱
     * @param newEmail 待改绑的新邮箱；可为 {@code null}，非空时需通过邮箱格式校验且不超过 128 字符
     */
    public void setNewEmail(final String newEmail) {
        this.newEmail = newEmail;
    }

    /**
     * 替换验证码
     * @param code 发往新邮箱的 6 位验证码；可为 {@code null}，非空时长度必须恰好为 6
     */
    public void setCode(final String code) {
        this.code = code;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ChangeEmailVerifyDTO)) return false;
        final ChangeEmailVerifyDTO other = (ChangeEmailVerifyDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisNewEmail = this.getNewEmail();
        final Object otherNewEmail = other.getNewEmail();
        if (thisNewEmail == null ? otherNewEmail != null : !thisNewEmail.equals(otherNewEmail)) return false;
        final Object thisCode = this.getCode();
        final Object otherCode = other.getCode();
        if (thisCode == null ? otherCode != null : !thisCode.equals(otherCode)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ChangeEmailVerifyDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashNewEmail = this.getNewEmail();
        result = result * PRIME + (hashNewEmail == null ? 43 : hashNewEmail.hashCode());
        final Object hashCode = this.getCode();
        result = result * PRIME + (hashCode == null ? 43 : hashCode.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ChangeEmailVerifyDTO(newEmail=" + this.getNewEmail() + ", code=" + this.getCode() + ")";
    }
}
