package top.zhaizz.client.service;

import top.zhaizz.pojo.dto.auth.ChangePasswordDTO;
import top.zhaizz.pojo.dto.user.UpdateUserDTO;
import top.zhaizz.pojo.vo.user.UserVO;

/** 用户信息服务接口。 */
public interface ClientUserService {

    /**
     * 根据 ID 获取用户信息。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @return 用户展示信息，不包含密码
     * @throws top.zhaizz.common.exception.BizException 用户不存在时为 NOT_FOUND
     */
    UserVO getUserById(Long userId);

    /**
     * 更新用户信息。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param request 待更新的昵称和头像
     * @return 更新昵称和头像后的用户展示信息
     * @throws top.zhaizz.common.exception.BizException 用户不存在时为 NOT_FOUND
     */
    UserVO updateUser(Long userId, UpdateUserDTO request);

    /**
     * <p>更新密码后撤销该用户全部会话。
     * 修改密码。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param request 旧密码和新密码
     * @throws top.zhaizz.common.exception.BizException 用户不存在时为 NOT_FOUND，旧密码错误时为 UNAUTHORIZED
     */
    void changePassword(Long userId, ChangePasswordDTO request);
}
