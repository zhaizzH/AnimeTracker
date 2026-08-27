package top.zhaizz.client.model;

import top.zhaizz.pojo.vo.auth.LoginVO;

/** 对外返回体与仅服务端使用的 refresh cookie 材料。 */
public record IssuedAuthSession(LoginVO body, String refreshToken, long refreshMaxAgeSeconds) {
}