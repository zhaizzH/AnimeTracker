package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.UserConverter;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.client.service.ClientUserService;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.pojo.dto.UpdateUserDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.UserVO;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class ClientUserServiceImpl implements ClientUserService {

    private final UserMapper userMapper;

    @Override
    public UserVO getUserById(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }
        return UserConverter.toUserVO(user);
    }

    @Override
    public UserVO updateUser(Long userId, UpdateUserDTO request) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }
        UserConverter.updateFromRequest(user, request);
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);
        return UserConverter.toUserVO(user);
    }
}
