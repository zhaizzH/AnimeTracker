package top.zhaizz.user.converter;

import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.UserVO;

/**
 * 用户实体 ↔ VO 转换器
 *
 * <p>职责：
 * <ul>
 *   <li>{@link User} → {@link UserVO}（排除 password 字段）</li>
 *   <li>{@link UpdateUserDTO} → 部分更新 {@link User}（合并非空字段）</li>
 * </ul>
 */
public class UserConverter {

    private UserConverter() {}

    /**
     * 将 User 实体转换为 UserVO（不含 password）
     */
    public static UserVO toUserVO(User entity) {
        if (entity == null) return null;
        UserVO vo = new UserVO();
        vo.setId(entity.getId());
        vo.setUsername(entity.getUsername());
        vo.setEmail(entity.getEmail());
        vo.setNickname(entity.getNickname());
        vo.setAvatar(entity.getAvatar());
        vo.setRole(entity.getRole());
        vo.setCreatedAt(entity.getCreatedAt());
        return vo;
    }

    /**
     * 将 UpdateUserRequest 的非空字段合并到已有 User 实体
     */
    public static void updateFromRequest(User user, UpdateUserDTO request) {
        if (request.getNickname() != null) {
            user.setNickname(request.getNickname());
        }
        if (request.getAvatar() != null) {
            user.setAvatar(request.getAvatar());
        }
        if (request.getEmail() != null) {
            user.setEmail(request.getEmail());
        }
    }
}
