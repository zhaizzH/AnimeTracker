package top.zhaizz.auth.security;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;

import java.util.Collection;
import java.util.List;

/**
 * 封装 Spring Security 身份主体与单项业务角色，不携带密码或令牌
 */
@Getter
@AllArgsConstructor
public class UserPrincipal implements Authentication {

    /** 认证成功的用户 ID，作为 principal 返回 */
    private Long userId;
    /** 不带 ROLE_ 前缀的业务角色 */
    private String role;
    /** 是否已由过滤器完成认证，初始为 false */
    private boolean authenticated = false;

    /**
     * 创建尚未标记认证成功的身份
     * @param userId 用户 ID
     * @param role 不带 ROLE_ 前缀的角色
     */
    public UserPrincipal(Long userId, String role) {
        this.userId = userId;
        this.role = role;
    }

    /**
     * 返回由业务角色加 ROLE_ 前缀得到的单项权限集合
     * @return 单项角色权限集合
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(() -> "ROLE_" + role);
    }

    /**
     * 不保存密码或令牌凭据
     * @return 始终为 null
     */
    @Override
    public Object getCredentials() {
        return null;
    }

    /**
     * 不携带额外认证详情
     * @return 始终为 null
     */
    @Override
    public Object getDetails() {
        return null;
    }

    /**
     * 返回用户 ID 作为身份主体
     * @return 用户 ID
     */
    @Override
    public Object getPrincipal() {
        return userId;
    }

    /**
     * 读取过滤器设置的认证结果
     * @return 已确认认证时为 true
     */
    @Override
    public boolean isAuthenticated() {
        return authenticated;
    }

    /**
     * 设置认证结果
     * @param isAuthenticated 是否已经完成认证
     */
    @Override
    public void setAuthenticated(boolean isAuthenticated) throws IllegalArgumentException {
        this.authenticated = isAuthenticated;
    }

    /**
     * 将用户 ID 表示为认证名称
     * @return 用户 ID 的字符串表示
     */
    @Override
    public String getName() {
        return String.valueOf(userId);
    }
}
