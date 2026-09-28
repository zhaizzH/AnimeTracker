package top.zhaizz.pojo.vo.auth;

import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 登录/验证结果（access token + 用户信息；refresh token 仅通过 HttpOnly Cookie 返回）
 */
public class LoginVO {

    /** 认证或会话令牌 */
    private String token;
    /** 认证成功后的用户信息 */
    private UserVO user;

    /**
     * 创建携带全部字段的登录结果
     * @param token 认证或会话令牌，可为 {@code null}
     * @param user 认证成功后的用户信息，可为 {@code null}
     */
    public LoginVO(final String token, final UserVO user) {
        this.token = token;
        this.user = user;
    }

    /**
     * 获取认证或会话令牌
     * @return 供客户端后续请求携带的访问令牌；未提供时为 {@code null}
     */
    public String getToken() {
        return this.token;
    }

    /**
     * 获取认证成功后的用户信息
     * @return 当前登录用户的公开信息；未提供时为 {@code null}
     */
    public UserVO getUser() {
        return this.user;
    }

    /**
     * 替换认证或会话令牌
     * @param token 供客户端后续请求携带的访问令牌，可为 {@code null}
     */
    public void setToken(final String token) {
        this.token = token;
    }

    /**
     * 替换认证成功后的用户信息
     * @param user 当前登录用户的公开信息，可为 {@code null}
     */
    public void setUser(final UserVO user) {
        this.user = user;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LoginVO)) return false;
        final LoginVO other = (LoginVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisToken = this.getToken();
        final Object otherToken = other.getToken();
        if (thisToken == null ? otherToken != null : !thisToken.equals(otherToken)) return false;
        final Object thisUser = this.getUser();
        final Object otherUser = other.getUser();
        if (thisUser == null ? otherUser != null : !thisUser.equals(otherUser)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof LoginVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashToken = this.getToken();
        result = result * PRIME + (hashToken == null ? 43 : hashToken.hashCode());
        final Object hashUser = this.getUser();
        result = result * PRIME + (hashUser == null ? 43 : hashUser.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "LoginVO(token=" + this.getToken() + ", user=" + this.getUser() + ")";
    }
}
