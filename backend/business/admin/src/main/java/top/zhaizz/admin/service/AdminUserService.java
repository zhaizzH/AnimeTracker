package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.user.UserVO;

/**
 * 用户管理服务接口。
 */
public interface AdminUserService {
    /**
     * 分页查询所有用户。
     * @param page 分页页码，从 1 开始
     * @param size 每页记录数
     * @return 按注册时间降序排列的用户分页
     */
    PageResult<UserVO> listUsers(int page, int size);
    /**
     * <p>更新成功后撤销该用户全部会话。
     * 修改指定用户的角色。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param role 目标用户角色
     * @return 修改角色后的用户信息
     * @throws top.zhaizz.common.exception.BizException 用户不存在时为 NOT_FOUND，目标为超级管理员时为 FORBIDDEN
     */
    UserVO updateUserRole(Long userId, String role);
    /**
     * <p>禁用账户时撤销全部会话，启用时不撤销。
     * 修改指定用户的启用状态。
     *
     * @param userId 用户 ID
     * @param enabled 是否允许用户登录和使用服务
     * @return 更新后的用户展示对象
     * @throws top.zhaizz.common.exception.BizException 用户不存在时为 NOT_FOUND，禁用超级管理员时为 FORBIDDEN
     */
    UserVO updateUserEnabled(Long userId, boolean enabled);
}
