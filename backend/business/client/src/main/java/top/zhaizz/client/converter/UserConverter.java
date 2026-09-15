package top.zhaizz.client.converter;

import top.zhaizz.pojo.dto.user.UpdateUserDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 用户转换器
 */
public class UserConverter {
    /**
     * 禁止实例化仅提供静态操作的工具类
     */
    private UserConverter() {}

    /**
     * 将账户转换为展示对象，省略密码等认证材料
     * @param entity 用户实体，允许为 {@code null}
     * @return 新的用户展示对象；输入为空时返回 {@code null}，不修改实体
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
        vo.setEnabled(entity.getEnabled());
        vo.setCreatedAt(entity.getCreatedAt());
        return vo;
    }

    /**
     * 将非空昵称和头像覆盖到用户实体，其余字段保持原值
     * @param user 待修改的用户实体，非空
     * @param request 更新内容，非空；字段为空表示保留原值
     * @throws NullPointerException 请求为空，或目标用户为空且有字段需要更新
     */
    public static void updateFromRequest(User user, UpdateUserDTO request) {
        if (request.getNickname() != null) user.setNickname(request.getNickname());
        if (request.getAvatar() != null) user.setAvatar(request.getAvatar());
    }
}
