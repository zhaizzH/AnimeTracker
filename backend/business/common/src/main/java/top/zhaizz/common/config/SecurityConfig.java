package top.zhaizz.common.config;

import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import top.zhaizz.common.security.JwtAuthenticationFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfigurationSource;

/**
 * 安全配置类
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {
    // JWT 认证过滤器
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    // CORS 配置源
    private final CorsConfigurationSource corsConfigurationSource;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .cors(cors -> cors.configurationSource(corsConfigurationSource))
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        // 公开接口：无需认证（注册、登录、邮箱验证）
                        .requestMatchers("/api/user/auth/register", "/api/user/auth/login",
                                "/api/user/auth/verify-email", "/api/user/auth/resend-code").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/user/subjects/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/user/tags/**").permitAll()

                        // 管理接口：需 ADMIN 角色
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        // 用户接口：需认证
                        .requestMatchers("/api/user/**").authenticated()
                        // 文件上传：需认证
                        .requestMatchers("/api/common/files/**").authenticated()
                        .anyRequest().permitAll()
                )
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
