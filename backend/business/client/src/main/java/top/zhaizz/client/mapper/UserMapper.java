package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.User;

public interface UserMapper extends BaseMapper<User> {
    default boolean existsByUsername(String username) {
        return selectCount(new LambdaQueryWrapper<User>().eq(User::getUsername, username)) > 0;
    }
    default boolean existsByEmail(String email) {
        return selectCount(new LambdaQueryWrapper<User>().eq(User::getEmail, email)) > 0;
    }
}
