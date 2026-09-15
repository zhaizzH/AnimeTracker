package top.zhaizz.admin.converter;

import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 用户相关对象转换器
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
}
