package top.zhaizz.pojo.vo.user;

import java.time.LocalDateTime;

/**
 * 用户信息 VO（不含密码）
 */
public class UserVO {

    /** 用户ID */
    private Long id;            // 用户ID
    /** 用户名（唯一） */
    private String username;    // 用户名（唯一）
    /** 邮箱 */
    private String email;       // 邮箱
    /** 昵称 */
    private String nickname;    // 昵称
    /** 头像URL */
    private String avatar;      // 头像URL
    /** 角色: USER=普通用户, ADMIN=管理员 */
    private String role;        // 角色: USER=普通用户, ADMIN=管理员
    /** 账号是否启用 */
    private Boolean enabled;    // 账号是否启用
    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 创建字段均为默认值的空用户信息 */
    public UserVO() {
    }

    /**
     * 获取用户ID
     * @return 用户主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取用户名
     * @return 唯一用户名；未提供时为 {@code null}
     */
    public String getUsername() {
        return this.username;
    }

    /**
     * 获取邮箱
     * @return 邮箱地址；未提供时为 {@code null}
     */
    public String getEmail() {
        return this.email;
    }

    /**
     * 获取昵称
     * @return 昵称，未设置时展示用户名；未提供时为 {@code null}
     */
    public String getNickname() {
        return this.nickname;
    }

    /**
     * 获取头像URL
     * @return 头像地址；未提供时为 {@code null}
     */
    public String getAvatar() {
        return this.avatar;
    }

    /**
     * 获取角色
     * @return 角色文本；USER=普通用户, ADMIN=管理员，未提供时为 {@code null}
     */
    public String getRole() {
        return this.role;
    }

    /**
     * 获取账号是否启用
     * @return 账号启用时为 {@code true}；未提供时为 {@code null}
     */
    public Boolean getEnabled() {
        return this.enabled;
    }

    /**
     * 获取创建时间
     * @return 账号创建时间；未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 替换用户ID
     * @param id 用户主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换用户名
     * @param username 唯一用户名，可为 {@code null}
     */
    public void setUsername(final String username) {
        this.username = username;
    }

    /**
     * 替换邮箱
     * @param email 邮箱地址，可为 {@code null}
     */
    public void setEmail(final String email) {
        this.email = email;
    }

    /**
     * 替换昵称
     * @param nickname 昵称，可为 {@code null}
     */
    public void setNickname(final String nickname) {
        this.nickname = nickname;
    }

    /**
     * 替换头像URL
     * @param avatar 头像地址，可为 {@code null}
     */
    public void setAvatar(final String avatar) {
        this.avatar = avatar;
    }

    /**
     * 替换角色
     * @param role 角色文本；USER=普通用户, ADMIN=管理员，可为 {@code null}
     */
    public void setRole(final String role) {
        this.role = role;
    }

    /**
     * 替换账号是否启用
     * @param enabled 账号启用时为 {@code true}，可为 {@code null}
     */
    public void setEnabled(final Boolean enabled) {
        this.enabled = enabled;
    }

    /**
     * 替换创建时间
     * @param createdAt 账号创建时间，可为 {@code null}
     */
    public void setCreatedAt(final LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof UserVO)) return false;
        final UserVO other = (UserVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisEnabled = this.getEnabled();
        final Object otherEnabled = other.getEnabled();
        if (thisEnabled == null ? otherEnabled != null : !thisEnabled.equals(otherEnabled)) return false;
        final Object thisUsername = this.getUsername();
        final Object otherUsername = other.getUsername();
        if (thisUsername == null ? otherUsername != null : !thisUsername.equals(otherUsername)) return false;
        final Object thisEmail = this.getEmail();
        final Object otherEmail = other.getEmail();
        if (thisEmail == null ? otherEmail != null : !thisEmail.equals(otherEmail)) return false;
        final Object thisNickname = this.getNickname();
        final Object otherNickname = other.getNickname();
        if (thisNickname == null ? otherNickname != null : !thisNickname.equals(otherNickname)) return false;
        final Object thisAvatar = this.getAvatar();
        final Object otherAvatar = other.getAvatar();
        if (thisAvatar == null ? otherAvatar != null : !thisAvatar.equals(otherAvatar)) return false;
        final Object thisRole = this.getRole();
        final Object otherRole = other.getRole();
        if (thisRole == null ? otherRole != null : !thisRole.equals(otherRole)) return false;
        final Object thisCreatedAt = this.getCreatedAt();
        final Object otherCreatedAt = other.getCreatedAt();
        if (thisCreatedAt == null ? otherCreatedAt != null : !thisCreatedAt.equals(otherCreatedAt)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof UserVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashId = this.getId();
        result = result * PRIME + (hashId == null ? 43 : hashId.hashCode());
        final Object hashEnabled = this.getEnabled();
        result = result * PRIME + (hashEnabled == null ? 43 : hashEnabled.hashCode());
        final Object hashUsername = this.getUsername();
        result = result * PRIME + (hashUsername == null ? 43 : hashUsername.hashCode());
        final Object hashEmail = this.getEmail();
        result = result * PRIME + (hashEmail == null ? 43 : hashEmail.hashCode());
        final Object hashNickname = this.getNickname();
        result = result * PRIME + (hashNickname == null ? 43 : hashNickname.hashCode());
        final Object hashAvatar = this.getAvatar();
        result = result * PRIME + (hashAvatar == null ? 43 : hashAvatar.hashCode());
        final Object hashRole = this.getRole();
        result = result * PRIME + (hashRole == null ? 43 : hashRole.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "UserVO(id=" + this.getId() + ", username=" + this.getUsername() + ", email=" + this.getEmail() + ", nickname=" + this.getNickname() + ", avatar=" + this.getAvatar() + ", role=" + this.getRole() + ", enabled=" + this.getEnabled() + ", createdAt=" + this.getCreatedAt() + ")";
    }
}
