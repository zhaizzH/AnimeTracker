package top.zhaizz.animetracker.common.vo;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户信息 VO（不含密码）
 */
@Data
public class UserVO {

    private Long id;
    private String username;
    private String email;
    private String nickname;
    private String avatar;
    private String role;        // USER / ADMIN
    private LocalDateTime createdAt;
}
