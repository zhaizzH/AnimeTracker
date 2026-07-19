package top.zhaizz.user.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.User;

/**
 * 用户 Mapper
 */
public interface UserMapper extends BaseMapper<User> {

    /**
     * 根据用户名查询是否存在
     */
    default boolean existsByUsername(String username) {
        return selectCount(new LambdaQueryWrapper<User>()
                .eq(User::getUsername, username)) > 0;
    }

    /**
     * 根据邮箱查询是否存在
     */
    default boolean existsByEmail(String email) {
        return selectCount(new LambdaQueryWrapper<User>()
                .eq(User::getEmail, email)) > 0;
    }
}
