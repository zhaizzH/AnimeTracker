package top.zhaizz.client.service;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Service;

import jakarta.servlet.http.HttpServletResponse;
import top.zhaizz.client.config.AuthCookieProperties;

import java.time.Duration;

@Service
@RequiredArgsConstructor
public class RefreshCookieService {
    private final AuthCookieProperties properties;

    public void add(HttpServletResponse response, String token, long maxAgeSeconds) {
        response.addHeader("Set-Cookie", ResponseCookie.from(properties.getName(), token)
                .httpOnly(true)
                .secure(properties.isSecure())
                .sameSite(properties.getSameSite())
                .path(properties.getPath())
                .maxAge(Duration.ofSeconds(maxAgeSeconds))
                .build().toString());
    }

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