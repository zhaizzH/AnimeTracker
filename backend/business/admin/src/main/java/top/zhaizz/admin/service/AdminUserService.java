package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.UserVO;

/**
 * 用户管理服务接口
 */
public interface AdminUserService {
    /**
     * 分页查询所有用户
     */
    PageResult<UserVO> listUsers(int page, int size);
    /**
     * 修改指定用户的角色
     */
    UserVO updateUserRole(Long userId, String role);
}
