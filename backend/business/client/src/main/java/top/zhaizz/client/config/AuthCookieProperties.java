package top.zhaizz.client.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/** AuthCookieProperties 应用配置组件 */
@Component
@Data
@ConfigurationProperties(prefix = "at.auth.refresh-cookie")
public class AuthCookieProperties {
    /** refresh Cookie 名称 */
    private String name = "at_refresh";
    /** refresh Cookie 路径 */
    private String path = "/api/client/auth";
    /** 是否仅通过 HTTPS 发送 Cookie */
    private boolean secure = true;
    /** Cookie 的 SameSite 策略 */
    private String sameSite = "Lax";
}
