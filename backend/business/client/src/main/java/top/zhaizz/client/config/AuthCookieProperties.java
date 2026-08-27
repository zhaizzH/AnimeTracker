package top.zhaizz.client.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@Data
@ConfigurationProperties(prefix = "at.auth.refresh-cookie")
public class AuthCookieProperties {
    private String name = "at_refresh";
    private String path = "/api/client/auth";
    private boolean secure = true;
    private String sameSite = "Lax";
}