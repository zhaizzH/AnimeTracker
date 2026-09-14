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
import top.zhaizz.auth.security.CookieOriginFilter;
import top.zhaizz.auth.security.JwtAuthenticationFilter;

import java.io.IOException;

/**
 * Spring Security 运行时策略：无状态 JWT 认证、接口放行与角色鉴权。
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {
    /** JWT 请求认证过滤器。 */
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    /** Cookie 请求来源校验过滤器。 */
    private final CookieOriginFilter cookieOriginFilter;
    /** CORS 配置源。 */
    private final CorsConfigurationSource corsConfigurationSource;
    /** 应用共用的 JSON 序列化器。 */
    private final ObjectMapper objectMapper;

    /**
     * 配置无状态 JWT 安全过滤链；未显式匹配的 URL 默认拒绝。
     *
     * @param http Spring Security HTTP 安全构建器
     * @return 无状态认证与授权过滤链
     * @throws Exception 过滤链构建失败时抛出
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
                        .requestMatchers("/actuator/health", "/actuator/health/**").permitAll()
                        .requestMatchers("/api/client/auth/register", "/api/client/auth/login",
                                "/api/client/auth/verify-email", "/api/client/auth/resend-code",
                                "/api/client/auth/refresh",
                                "/api/client/auth/forgot-password", "/api/client/auth/reset-password", "/api/client/auth/logout").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/client/subjects/**").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/client/subjects/batch").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/client/subjects/lexical-search").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/client/evidence/batch").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/client/evidence/resolve").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/client/tags/**").permitAll()
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        .requestMatchers("/api/client/**").authenticated()
                        .anyRequest().denyAll()
                )
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
                .addFilterBefore(cookieOriginFilter, JwtAuthenticationFilter.class);。

        return http.build();
    }

    /**
     * 提供 BCrypt 密码编码器
     *
     * @return 默认强度的 BCrypt 密码编码器
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * 直接写入安全层统一 JSON 响应，避免经过 Controller advice。
     *
     * @param response 待写入内容的 HTTP 响应
     * @param errorType 非空统一错误类型，提供错误码与默认提示
     * @throws IOException 响应流写入失败时抛出
     */
    private void writeJson(HttpServletResponse response, ErrorType errorType) throws IOException {
        int code = errorType.getCode();
        response.setStatus(code);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(objectMapper.writeValueAsString(Result.error(code, errorType.getMessage())));
    }
}
