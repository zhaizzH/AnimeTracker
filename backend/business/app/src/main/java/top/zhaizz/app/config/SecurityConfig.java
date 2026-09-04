package top.zhaizz.app.config;

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
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.security.CookieOriginFilter;
import top.zhaizz.common.security.JwtAuthenticationFilter;

import java.io.IOException;

/**
 * Spring Security 运行时策略：无状态 JWT 认证、接口放行与角色鉴权
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final CookieOriginFilter cookieOriginFilter;
    private final CorsConfigurationSource corsConfigurationSource;
    private final ObjectMapper objectMapper;

    /**
     * 配置无状态 JWT 安全过滤链；未显式匹配的 URL 默认拒绝
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
                        .requestMatchers("/api/client/auth/register", "/api/client/auth/login",
                                "/api/client/auth/verify-email", "/api/client/auth/resend-code",
                                "/api/client/auth/refresh",
                                "/api/client/auth/forgot-password", "/api/client/auth/reset-password", "/api/client/auth/logout").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/client/subjects/**").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/client/subjects/batch").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/client/evidence/batch").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/client/evidence/resolve").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/client/tags/**").permitAll()
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        .requestMatchers("/api/client/**").authenticated()
                        .anyRequest().denyAll()
                )
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
                .addFilterBefore(cookieOriginFilter, JwtAuthenticationFilter.class);

        return http.build();
    }

    /**
     * 提供 BCrypt 密码编码器
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * 直接写入安全层统一 JSON 响应，避免经过 Controller advice
     */
    private void writeJson(HttpServletResponse response, ErrorType errorType) throws IOException {
        int code = errorType.getCode();
        response.setStatus(code);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(objectMapper.writeValueAsString(Result.error(code, errorType.getMessage())));
    }
}
