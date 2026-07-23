package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.vo.UserVO;

/** 用户信息服务接口 */
public interface ClientUserService {

    /** 根据 ID 获取用户信息 */
    UserVO getUserById(Long userId);

    /** 更新用户信息 */
    UserVO updateUser(Long userId, UpdateUserDTO request);
}
