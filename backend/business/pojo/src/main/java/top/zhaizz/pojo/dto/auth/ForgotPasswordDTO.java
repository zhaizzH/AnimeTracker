package top.zhaizz.pojo.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

/**
 * 忘记密码 — 发送重置验证码请求 DTO
 */
public class ForgotPasswordDTO {
    /**
     * 邮箱
     */
    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email; // 邮箱

    /** 创建字段均为默认值的空请求对象 */
    public ForgotPasswordDTO() {
    }

    /**
     * 获取邮箱
     * @return 接收重置验证码的邮箱；未提供时为 {@code null}，必填且需通过邮箱格式校验
     */
    public String getEmail() {
        return this.email;
    }

    /**
     * 替换邮箱
     * @param email 接收重置验证码的邮箱；可为 {@code null}，非空时需通过邮箱格式校验
     */
    public void setEmail(final String email) {
        this.email = email;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ForgotPasswordDTO)) return false;
        final ForgotPasswordDTO other = (ForgotPasswordDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisEmail = this.getEmail();
        final Object otherEmail = other.getEmail();
        if (thisEmail == null ? otherEmail != null : !thisEmail.equals(otherEmail)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ForgotPasswordDTO;
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
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ForgotPasswordDTO(email=" + this.getEmail() + ")";
    }
}
