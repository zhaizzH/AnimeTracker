package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.User;

/** 用户 Mapper */
public interface UserMapper extends BaseMapper<User> {
    /** 检查用户名是否已存在 */
    default boolean existsByUsername(String username) {
        return selectCount(new LambdaQueryWrapper<User>().eq(User::getUsername, username)) > 0;
    }
    /** 检查邮箱是否已存在 */
    default boolean existsByEmail(String email) {
        return selectCount(new LambdaQueryWrapper<User>().eq(User::getEmail, email)) > 0;
    }
}
