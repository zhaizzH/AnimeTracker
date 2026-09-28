package top.zhaizz.client.service;

import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Service;

import jakarta.servlet.http.HttpServletResponse;
import top.zhaizz.client.config.AuthCookieProperties;

import java.time.Duration;

/**
 * RefreshCookieService 业务服务
 */
@Service
public class RefreshCookieService {
    /**
     * refresh Cookie 配置
     */
    private final AuthCookieProperties properties;

    /**
     * 注入 refresh Cookie 配置
     * @param properties 提供 Cookie 名称、路径、Secure 与 SameSite 的配置组件，由 Spring 容器提供
     */
    public RefreshCookieService(final AuthCookieProperties properties) {
        this.properties = properties;
    }

    /**
     * 将 refresh token 按配置写入响应 Cookie
     * @param response 用于写入 Cookie 的 HTTP 响应
     * @param token 待写入 Cookie 的刷新令牌
     * @param maxAgeSeconds Cookie 有效期，单位为秒
     */
    public void add(HttpServletResponse response, String token, long maxAgeSeconds) {
        response.addHeader("Set-Cookie", ResponseCookie.from(properties.getName(), token)
                .httpOnly(true)
                .secure(properties.isSecure())
                .sameSite(properties.getSameSite())
                .path(properties.getPath())
                .maxAge(Duration.ofSeconds(maxAgeSeconds))
                .build().toString());
    }

    /**
     * 通过过期 Cookie 清除客户端保存的 refresh token
     * @param response 用于写入 Cookie 的 HTTP 响应
     */
    public void clear(HttpServletResponse response) {
        response.addHeader("Set-Cookie", ResponseCookie.from(properties.getName(), "")
                .httpOnly(true)
                .secure(properties.isSecure())
                .sameSite(properties.getSameSite())
                .path(properties.getPath())
                .maxAge(Duration.ZERO)
                .build().toString());
    }
}
