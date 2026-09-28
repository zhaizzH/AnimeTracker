package top.zhaizz.pojo.dto.auth;

import jakarta.validation.constraints.NotBlank;

/**
 * 登录请求 DTO
 */
public class LoginDTO {
    /**
     * 用户名或邮箱
     */
    @NotBlank(message = "用户名或邮箱不能为空")
    private String username; // 用户名或邮箱
    /**
     * 密码
     */
    @NotBlank(message = "密码不能为空")
    private String password; // 密码

    /** 创建字段均为默认值的空请求对象 */
    public LoginDTO() {
    }

    /**
     * 创建携带全部字段的登录请求
     * @param username 用户名或邮箱，可为 {@code null}，校验要求其非空
     * @param password 密码，可为 {@code null}，校验要求其非空
     */
    public LoginDTO(final String username, final String password) {
        this.username = username;
        this.password = password;
    }

    /**
     * 获取用户名或邮箱
     * @return 登录账号，可填用户名或邮箱；未提供时为 {@code null}，必填
     */
    public String getUsername() {
        return this.username;
    }

    /**
     * 获取密码
     * @return 登录密码明文；未提供时为 {@code null}，必填
     */
    public String getPassword() {
        return this.password;
    }

    /**
     * 替换用户名或邮箱
     * @param username 登录账号，可填用户名或邮箱；可为 {@code null}，但校验要求其非空
     */
    public void setUsername(final String username) {
        this.username = username;
    }

    /**
     * 替换密码
     * @param password 登录密码明文；可为 {@code null}，但校验要求其非空
     */
    public void setPassword(final String password) {
        this.password = password;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LoginDTO)) return false;
        final LoginDTO other = (LoginDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisUsername = this.getUsername();
        final Object otherUsername = other.getUsername();
        if (thisUsername == null ? otherUsername != null : !thisUsername.equals(otherUsername)) return false;
        final Object thisPassword = this.getPassword();
        final Object otherPassword = other.getPassword();
        if (thisPassword == null ? otherPassword != null : !thisPassword.equals(otherPassword)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof LoginDTO;
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
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "LoginDTO(username=" + this.getUsername() + ", password=" + this.getPassword() + ")";
    }
}
