package top.zhaizz.client.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * refresh Cookie 相关配置项，绑定 at.auth.refresh-cookie 前缀
 */
@Component
@ConfigurationProperties(prefix = "at.auth.refresh-cookie")
public class AuthCookieProperties {
    /**
     * 写入 refresh token 的 Cookie 名称
     */
    private String name = "at_refresh";
    /**
     * refresh Cookie 生效的请求路径前缀
     */
    private String path = "/api/client/auth";
    /**
     * 是否仅允许通过 HTTPS 发送该 Cookie
     */
    private boolean secure = true;
    /**
     * Cookie 的 SameSite 策略，控制跨站请求时的发送行为
     */
    private String sameSite = "Lax";

    /** 创建使用默认配置值的空实例供 Spring 绑定 */
    public AuthCookieProperties() {
    }

    /**
     * 获取 refresh Cookie 名称
     * @return 用于标识 refresh token 的 Cookie 名
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取 refresh Cookie 路径
     * @return Cookie 生效的请求路径前缀
     */
    public String getPath() {
        return this.path;
    }

    /**
     * 判断是否仅通过 HTTPS 发送 Cookie
     * @return 仅 HTTPS 发送时为 {@code true}
     */
    public boolean isSecure() {
        return this.secure;
    }

    /**
     * 获取 Cookie 的 SameSite 策略
     * @return SameSite 取值，如 Lax、Strict 或 None
     */
    public String getSameSite() {
        return this.sameSite;
    }

    /**
     * 替换 refresh Cookie 名称
     * @param name 新的 Cookie 名，供 Spring 绑定时写入
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换 refresh Cookie 路径
     * @param path 新的请求路径前缀，供 Spring 绑定时写入
     */
    public void setPath(final String path) {
        this.path = path;
    }

    /**
     * 设置是否仅通过 HTTPS 发送 Cookie
     * @param secure 仅 HTTPS 发送时为 {@code true}，供 Spring 绑定时写入
     */
    public void setSecure(final boolean secure) {
        this.secure = secure;
    }

    /**
     * 替换 Cookie 的 SameSite 策略
     * @param sameSite 新的 SameSite 取值，供 Spring 绑定时写入
     */
    public void setSameSite(final String sameSite) {
        this.sameSite = sameSite;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部配置字段
     * @param o 待比较的对象
     * @return 类型与全部配置字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof AuthCookieProperties)) return false;
        final AuthCookieProperties other = (AuthCookieProperties) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.isSecure() != other.isSecure()) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisPath = this.getPath();
        final Object otherPath = other.getPath();
        if (thisPath == null ? otherPath != null : !thisPath.equals(otherPath)) return false;
        final Object thisSameSite = this.getSameSite();
        final Object otherSameSite = other.getSameSite();
        if (thisSameSite == null ? otherSameSite != null : !thisSameSite.equals(otherSameSite)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof AuthCookieProperties;
    }

    /**
     * 基于本类全部配置字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + (this.isSecure() ? 79 : 97);
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashPath = this.getPath();
        result = result * PRIME + (hashPath == null ? 43 : hashPath.hashCode());
        final Object hashSameSite = this.getSameSite();
        result = result * PRIME + (hashSameSite == null ? 43 : hashSameSite.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部配置字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "AuthCookieProperties(name=" + this.getName() + ", path=" + this.getPath() + ", secure=" + this.isSecure() + ", sameSite=" + this.getSameSite() + ")";
    }
}
