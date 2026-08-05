package top.zhaizz.common.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfigurationSource;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.security.JwtAuthenticationFilter;

import java.io.IOException;

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
    // 统一 JSON 序列化
    private final ObjectMapper objectMapper;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .cors(cors -> cors.configurationSource(corsConfigurationSource))
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .exceptionHandling(ex -> ex
                        .authenticationEntryPoint((request, response, authException) ->
                                writeJson(response, 401, "未认证或登录已过期"))
                        .accessDeniedHandler((request, response, accessDeniedException) ->
                                writeJson(response, 403, "无权限")))
                .authorizeHttpRequests(auth -> auth
                        // 公开接口：无需认证（注册、登录、邮箱验证）
                        .requestMatchers("/api/user/auth/register", "/api/user/auth/login",
                                "/api/user/auth/verify-email", "/api/user/auth/resend-code",
                                "/api/user/auth/refresh",
                                "/api/user/auth/forgot-password", "/api/user/auth/reset-password").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/user/subjects/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/user/tags/**").permitAll()

                        // 管理接口：需 ADMIN 角色
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        // 用户接口：需认证
                        .requestMatchers("/api/user/**").authenticated()
                        // 文件上传：需认证
                        .requestMatchers("/api/common/files/**").authenticated()
                        // Agent 代理：需认证
                        .requestMatchers("/api/agent/**").authenticated()
                        .anyRequest().permitAll()
                )
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /** 安全层统一 JSON 响应（绕过 @RestControllerAdvice，直接写 Result） */
    private void writeJson(HttpServletResponse response, int code, String message) throws IOException {
        response.setStatus(code);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(objectMapper.writeValueAsString(Result.error(code, message)));
    }
}
