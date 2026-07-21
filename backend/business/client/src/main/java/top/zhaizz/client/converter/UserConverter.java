package top.zhaizz.client.converter;

import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.UserVO;

public class UserConverter {
    private UserConverter() {}

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

    public static void updateFromRequest(User user, UpdateUserDTO request) {
        if (request.getNickname() != null) user.setNickname(request.getNickname());
        if (request.getAvatar() != null) user.setAvatar(request.getAvatar());
    }
}
