package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户实体
 */
@Data
@TableName("user")
public class User {

    /** 用户ID */
    private Long id;                    // 用户ID
    /** 用户名（唯一） */
    private String username;            // 用户名（唯一）
    /** 密码（BCrypt 加密存储） */
    private String password;            // 密码（BCrypt 加密存储）
    /** 邮箱 */
    private String email;               // 邮箱
    /** 昵称 */
    private String nickname;            // 昵称
    /** 头像URL */
    private String avatar;              // 头像URL
    /** 角色: USER=普通用户, ADMIN=管理员 */
    private String role;                // 角色: USER=普通用户, ADMIN=管理员
    /** 邮箱是否已验证 */
    private Boolean emailVerified;      // 邮箱是否已验证
    /** 账号是否启用 */
    private Boolean enabled = true; // 账号是否启用
    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间
    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间
}
