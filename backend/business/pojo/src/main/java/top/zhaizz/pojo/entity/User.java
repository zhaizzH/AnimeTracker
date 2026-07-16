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

    private Long id;
    private String username;
    private String password;        // BCrypt 加密
    private String email;
    private String nickname;
    private String avatar;
    private String role;            // USER / ADMIN
    private Boolean emailVerified;  // 邮箱是否已验证
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
