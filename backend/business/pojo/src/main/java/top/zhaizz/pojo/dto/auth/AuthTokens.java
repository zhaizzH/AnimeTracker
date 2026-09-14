package top.zhaizz.pojo.dto.auth;

/**
 * 认证能力签发的内部凭据；刷新明文只能写入安全 Cookie，不得出现在响应体或日志。
 * @param accessToken 返回给调用端的访问令牌
 * @param refreshToken 仅服务端 Cookie 适配使用的刷新凭据
 * @param refreshMaxAgeSeconds 刷新 Cookie 寿命，单位秒，至少为 1
 */
public record AuthTokens(String accessToken, String refreshToken, long refreshMaxAgeSeconds) {
}
