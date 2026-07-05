package top.zhaizz.animetracker.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.animetracker.common.exception.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.user.converter.UserConverter;
import top.zhaizz.animetracker.common.dto.UpdateUserDTO;
import top.zhaizz.animetracker.common.entity.User;
import top.zhaizz.animetracker.user.mapper.UserMapper;
import top.zhaizz.animetracker.user.service.UserService;
import top.zhaizz.animetracker.common.vo.UserVO;

import java.time.LocalDateTime;
import java.util.stream.Collectors;

/**
 * 用户服务实现
 */
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

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

        // 合并非空字段到实体
        UserConverter.updateFromRequest(user, request);
        user.setUpdatedAt(LocalDateTime.now());

        userMapper.updateById(user);
        return UserConverter.toUserVO(user);
    }

    @Override
    public PageResult<UserVO> listUsers(int page, int size) {
        Page<User> mpPage = userMapper.selectPage(
                new Page<>(page, size),
                new LambdaQueryWrapper<User>().orderByDesc(User::getCreatedAt)
        );
        return PageResult.of(
                mpPage.getRecords().stream()
                        .map(UserConverter::toUserVO)
                        .collect(Collectors.toList()),
                mpPage.getTotal(),
                (int) mpPage.getCurrent(),
                (int) mpPage.getSize()
        );
    }

    @Override
    public UserVO updateUserRole(Long userId, String role) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }
        if(user.getId()==1){
            throw new BizException(ErrorType.FORBIDDEN, "管理员角色不能被修改");
        }
        user.setRole(role);
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);
        return UserConverter.toUserVO(user);
    }
}
