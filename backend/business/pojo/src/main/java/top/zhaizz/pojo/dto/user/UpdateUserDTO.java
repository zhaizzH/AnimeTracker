package top.zhaizz.pojo.dto.user;

import jakarta.validation.constraints.Size;

/**
 * 修改个人信息请求 DTO
 */
public class UpdateUserDTO {
    /**
     * 昵称
     */
    @Size(max = 64, message = "昵称长度不能超过64")
    private String nickname; // 昵称
    /**
     * 头像URL
     */
    @Size(max = 512, message = "头像URL长度不能超过512")
    private String avatar; // 头像URL

    /** 创建字段均可选的部分更新请求对象 */
    public UpdateUserDTO() {
    }

    /**
     * 获取昵称
     * @return 新昵称；为 {@code null} 时表示不更新昵称，非空时不超过 64 字符
     */
    public String getNickname() {
        return this.nickname;
    }

    /**
     * 获取头像URL
     * @return 新头像地址；为 {@code null} 时表示不更新头像，非空时不超过 512 字符
     */
    public String getAvatar() {
        return this.avatar;
    }

    /**
     * 替换昵称
     * @param nickname 新昵称；可为 {@code null} 表示不更新昵称，非空时不超过 64 字符
     */
    public void setNickname(final String nickname) {
        this.nickname = nickname;
    }

    /**
     * 替换头像URL
     * @param avatar 新头像地址；可为 {@code null} 表示不更新头像，非空时不超过 512 字符
     */
    public void setAvatar(final String avatar) {
        this.avatar = avatar;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof UpdateUserDTO)) return false;
        final UpdateUserDTO other = (UpdateUserDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisNickname = this.getNickname();
        final Object otherNickname = other.getNickname();
        if (thisNickname == null ? otherNickname != null : !thisNickname.equals(otherNickname)) return false;
        final Object thisAvatar = this.getAvatar();
        final Object otherAvatar = other.getAvatar();
        if (thisAvatar == null ? otherAvatar != null : !thisAvatar.equals(otherAvatar)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof UpdateUserDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashNickname = this.getNickname();
        result = result * PRIME + (hashNickname == null ? 43 : hashNickname.hashCode());
        final Object hashAvatar = this.getAvatar();
        result = result * PRIME + (hashAvatar == null ? 43 : hashAvatar.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "UpdateUserDTO(nickname=" + this.getNickname() + ", avatar=" + this.getAvatar() + ")";
    }
}
