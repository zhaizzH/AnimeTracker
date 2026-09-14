package top.zhaizz.pojo.vo.user;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户信息 VO（不含密码）。
 */
@Data
public class UserVO {

    /** 用户ID。 */
    private Long id;            // 用户ID
    /** 用户名（唯一）。 */
    private String username;    // 用户名（唯一）
    /** 邮箱。 */
    private String email;       // 邮箱
    /** 昵称。 */
    private String nickname;    // 昵称
    /** 头像URL。 */
    private String avatar;      // 头像URL
    /** 角色: USER=普通用户, ADMIN=管理员。 */
    private String role;        // 角色: USER=普通用户, ADMIN=管理员
    /** 账号是否启用。 */
    private Boolean enabled;    // 账号是否启用
    /** 创建时间。 */
    private LocalDateTime createdAt;    // 创建时间
}
