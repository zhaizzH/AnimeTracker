package top.zhaizz.user.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.vo.UserVO;

/**
 * 用户服务接口
 */
public interface UserService {

    /**
     * 获取用户信息
     */
    UserVO getUserById(Long userId);

    /**
     * 更新用户信息
     */
    UserVO updateUser(Long userId, UpdateUserDTO request);

    /**
     * 分页查询用户列表（管理员）
     */
    PageResult<UserVO> listUsers(int page, int size);

    /**
     * 修改用户角色（管理员）
     */
    UserVO updateUserRole(Long userId, String role);
}
