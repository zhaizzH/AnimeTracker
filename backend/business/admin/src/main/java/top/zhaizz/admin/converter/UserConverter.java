package top.zhaizz.admin.converter;

import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.UserVO;

/**
 * 用户相关对象转换器
 */
public class UserConverter {
    private UserConverter() {}

    /**
     * User 实体转为前端用户 VO
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
}
