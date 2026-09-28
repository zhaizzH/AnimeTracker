package top.zhaizz.pojo.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 注册请求 DTO
 */
public class RegisterDTO {
    /**
     * 用户名（唯一）
     */
    @NotBlank(message = "用户名不能为空")
    @Size(min = 1, max = 32, message = "用户名长度需在1~32之间")
    private String username; // 用户名（唯一）
    /**
     * 密码
     */
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 128, message = "密码长度需在6~128之间")
    private String password; // 密码
    /**
     * 邮箱
     */
    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    @Size(max = 128, message = "邮箱长度不能超过128")
    private String email; // 邮箱

    /** 创建字段均为默认值的空请求对象 */
    public RegisterDTO() {
    }

    /**
     * 获取用户名
     * @return 注册用户名；未提供时为 {@code null}，必填且长度需在 1~32 之间，全库唯一
     */
    public String getUsername() {
        return this.username;
    }

    /**
     * 获取密码
     * @return 注册密码明文；未提供时为 {@code null}，必填且长度需在 6~128 之间
     */
    public String getPassword() {
        return this.password;
    }

    /**
     * 获取邮箱
     * @return 注册邮箱；未提供时为 {@code null}，必填、需通过邮箱格式校验且不超过 128 字符
     */
    public String getEmail() {
        return this.email;
    }

    /**
     * 替换用户名
     * @param username 注册用户名；可为 {@code null}，非空时长度需在 1~32 之间且需保持唯一
     */
    public void setUsername(final String username) {
        this.username = username;
    }

    /**
     * 替换密码
     * @param password 注册密码明文；可为 {@code null}，非空时长度需在 6~128 之间
     */
    public void setPassword(final String password) {
        this.password = password;
    }

    /**
     * 替换邮箱
     * @param email 注册邮箱；可为 {@code null}，非空时需通过邮箱格式校验且不超过 128 字符
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
        if (!(o instanceof RegisterDTO)) return false;
        final RegisterDTO other = (RegisterDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisUsername = this.getUsername();
        final Object otherUsername = other.getUsername();
        if (thisUsername == null ? otherUsername != null : !thisUsername.equals(otherUsername)) return false;
        final Object thisPassword = this.getPassword();
        final Object otherPassword = other.getPassword();
        if (thisPassword == null ? otherPassword != null : !thisPassword.equals(otherPassword)) return false;
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
        return other instanceof RegisterDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashUsername = this.getUsername();
        result = result * PRIME + (hashUsername == null ? 43 : hashUsername.hashCode());
        final Object hashPassword = this.getPassword();
        result = result * PRIME + (hashPassword == null ? 43 : hashPassword.hashCode());
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
        return "RegisterDTO(username=" + this.getUsername() + ", password=" + this.getPassword() + ", email=" + this.getEmail() + ")";
    }
}
