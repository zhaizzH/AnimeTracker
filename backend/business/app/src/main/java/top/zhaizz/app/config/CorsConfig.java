package top.zhaizz.app.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import top.zhaizz.common.security.CookieOriginFilter;

import java.util.Arrays;
import java.util.List;

/**
 * CORS 跨域配置：仅放行白名单中的明确 Origin，刷新认证使用 HttpOnly Cookie，必须允许 credentialed 请求
 */
@Configuration
@EnableConfigurationProperties(CorsProperties.class)
public class CorsConfig {

    @Bean
    public CorsConfigurationSource corsConfigurationSource(CorsProperties corsProperties) {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(corsProperties.getAllowedOrigins());
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Request-ID"));
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", configuration);
        return source;
    }

    /** Cookie 认证端点的 Origin 白名单由应用装配层显式传入。 */
    @Bean
    public CookieOriginFilter cookieOriginFilter(CorsProperties corsProperties) {
        return new CookieOriginFilter(corsProperties.getAllowedOrigins());
    }
}
