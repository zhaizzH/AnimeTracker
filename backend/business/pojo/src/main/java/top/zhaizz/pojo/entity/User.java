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

    private Long id;                    // 用户ID
    private String username;            // 用户名（唯一）
    private String password;            // 密码（BCrypt 加密存储）
    private String email;               // 邮箱
    private String nickname;            // 昵称
    private String avatar;              // 头像URL
    private String role;                // 角色: USER=普通用户, ADMIN=管理员
    private Boolean emailVerified;      // 邮箱是否已验证
    private Boolean enabled = true; // 账号是否启用
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
}
