package top.zhaizz.pojo.dto.auth;

import top.zhaizz.pojo.vo.auth.LoginVO;

/**
 * 对外返回体与仅服务端使用的 refresh cookie 材料
 * @param body 登录响应体
 * @param refreshToken 仅写入 HttpOnly Cookie 的刷新凭据
 * @param refreshMaxAgeSeconds Cookie 最大寿命，单位秒
 */
public record IssuedAuthSession(LoginVO body, String refreshToken, long refreshMaxAgeSeconds) {
}

