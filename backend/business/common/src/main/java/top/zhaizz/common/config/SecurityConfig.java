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
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.security.JwtAuthenticationFilter;

import java.io.IOException;

/**
 * Spring Security 配置：无状态 JWT 认证、接口放行与角色鉴权
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final CorsConfigurationSource corsConfigurationSource;
    private final ObjectMapper objectMapper;

    /**
     * 配置无状态 JWT 安全过滤链：CORS、CSRF 关闭、接口放行与角色鉴权
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .cors(cors -> cors.configurationSource(corsConfigurationSource))
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .exceptionHandling(ex -> ex
                        .authenticationEntryPoint((request, response, authException) ->
                                writeJson(response, ErrorType.UNAUTHORIZED))
                        .accessDeniedHandler((request, response, accessDeniedException) ->
                                writeJson(response, ErrorType.FORBIDDEN)))
                .authorizeHttpRequests(auth -> auth
                        // 认证流程接口须先公开，否则无法登录注册
                        .requestMatchers("/api/user/auth/register", "/api/user/auth/login",
                                "/api/user/auth/verify-email", "/api/user/auth/resend-code",
                                "/api/user/auth/refresh",
                                "/api/user/auth/forgot-password", "/api/user/auth/reset-password").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/user/subjects/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/user/tags/**").permitAll()

                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        .requestMatchers("/api/user/**").authenticated()
                        .requestMatchers("/api/common/files/**").authenticated()
                        .requestMatchers("/api/client/agent/**").authenticated()
                        .anyRequest().permitAll()
                )
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * 密码加密器（BCrypt）
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /** 安全层统一 JSON 响应（绕过 @RestControllerAdvice，直接写 Result） */
    private void writeJson(HttpServletResponse response, ErrorType errorType) throws IOException {
        int code = errorType.getCode();
        response.setStatus(code);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(objectMapper.writeValueAsString(Result.error(code, errorType.getMessage())));
    }
}
