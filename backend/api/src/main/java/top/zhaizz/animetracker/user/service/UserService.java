package top.zhaizz.animetracker.user.service;

import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.common.dto.UpdateUserDTO;
import top.zhaizz.animetracker.common.vo.UserVO;

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
