package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.UserConverter;
import top.zhaizz.client.mapper.UserMapper;
import top.zhaizz.client.service.ClientUserService;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.auth.security.AuthSessionStore;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.pojo.dto.auth.ChangePasswordDTO;
import top.zhaizz.pojo.dto.user.UpdateUserDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.pojo.vo.user.UserVO;

import java.time.LocalDateTime;

/**
 * 用户信息服务实现。
 */
@Service
@RequiredArgsConstructor
public class ClientUserServiceImpl implements ClientUserService {

    /** 用户数据 Mapper。 */
    private final UserMapper userMapper;
    /** 密码哈希编解码器。 */
    private final PasswordEncoder passwordEncoder;
    /** 认证会话存储。 */
    private final AuthSessionStore sessionStore;

    /** {@inheritDoc} */
    @Override
    public UserVO getUserById(Long userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }
        return UserConverter.toUserVO(user);
    }

    /** {@inheritDoc} */
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

    /** {@inheritDoc} */
    @Override
    public void changePassword(Long userId, ChangePasswordDTO request) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }

        if (!passwordEncoder.matches(request.getOldPassword(), user.getPassword())) {
            throw new BizException(ErrorType.UNAUTHORIZED, "旧密码不正确");
        }

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);
        sessionStore.revokeAll(userId);
    }
}
