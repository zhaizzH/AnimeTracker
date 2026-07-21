package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.vo.UserVO;

public interface ClientUserService {

    UserVO getUserById(Long userId);

    UserVO updateUser(Long userId, UpdateUserDTO request);
}
