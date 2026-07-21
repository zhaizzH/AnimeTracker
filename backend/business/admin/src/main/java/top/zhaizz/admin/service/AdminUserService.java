package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.UserVO;

public interface AdminUserService {
    PageResult<UserVO> listUsers(int page, int size);
    UserVO updateUserRole(Long userId, String role);
}
