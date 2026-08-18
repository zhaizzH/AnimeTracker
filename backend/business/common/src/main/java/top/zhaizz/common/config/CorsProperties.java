package top.zhaizz.common.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

/**
 * CORS 跨域白名单配置（生产只允许 AT_CORS_ALLOWED_ORIGINS 中的明确来源，禁止通配符）
 */
@Data
@ConfigurationProperties(prefix = "at.cors")
public class CorsProperties {
    private List<String> allowedOrigins;
}
