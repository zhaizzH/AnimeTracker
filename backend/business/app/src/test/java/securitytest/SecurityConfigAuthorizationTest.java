package securitytest;

import org.junit.jupiter.api.Test;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.ApplicationContext;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import top.zhaizz.app.config.CorsConfig;
import top.zhaizz.app.config.SecurityConfig;
import top.zhaizz.auth.security.JwtAuthenticationFilter;
import org.springframework.security.web.SecurityFilterChain;

import static org.assertj.core.api.Assertions.assertThat;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Spring Security 路由认证与授权回归测试 */
@WebMvcTest(controllers = SecurityConfigAuthorizationTest.TestController.class)
@Import({SecurityConfig.class, CorsConfig.class})
@ContextConfiguration(classes = SecurityConfigAuthorizationTest.TestConfig.class)
@TestPropertySource(properties = "at.cors.allowed-origins[0]=http://allowed.test")
class SecurityConfigAuthorizationTest {

    /** 执行真实安全过滤链的模拟 HTTP 客户端 */
    @Autowired
    private MockMvc mvc;

    /** 用于断言安全过滤链只注册一次的测试上下文 */
    @Autowired
    private ApplicationContext applicationContext;

    /** 测试启动入口，避免加载完整业务基础设施 */
    @SpringBootConfiguration
    static class TestApplication {
    }

    /** 只注册授权测试需要的控制器和认证过滤器 */
    @TestConfiguration(proxyBeanMethods = false)
    static class TestConfig {
        /**
         * 注册覆盖公开和受保护路由的测试控制器
         * @return 独立的路由夹具
         */
        @Bean
        TestController testController() {
            return new TestController();
        }

        /**
         * 注册匿名请求不触发凭据存储的认证过滤器
         * @return 未连接外部认证依赖的过滤器
         */
        @Bean
        JwtAuthenticationFilter jwtAuthenticationFilter() {
            return new JwtAuthenticationFilter(null, null);
        }

    }

    /** 提供最小路由响应，以独立验证安全规则 */
    @RestController
    static class TestController {
        /**
         * 提供登录路由的固定响应
         * @return 用于断言授权通过的响应标记
         */
        @PostMapping("/api/client/auth/login")
        String login() {
            return "login";
        }

        /**
         * 提供公开条目路由的固定响应
         * @return 用于断言授权通过的响应标记
         */
        @GetMapping("/api/client/subjects/1")
        String publicSubject() {
            return "subject";
        }

        /**
         * 提供健康检查路由的固定响应
         * @return 用于断言授权通过的响应标记
         */
        @GetMapping("/actuator/health")
        String health() {
            return "ok";
        }

        /**
         * 提供批量证据路由的固定响应
         * @return 用于断言授权通过的响应标记
         */
        @PostMapping("/api/client/evidence/batch")
        String evidenceBatch() {
            return "evidence";
        }

        /**
         * 提供证据解析路由的固定响应
         * @return 用于断言授权通过的响应标记
         */
        @PostMapping("/api/client/evidence/resolve")
        String evidenceResolve() {
            return "evidence";
        }

        /**
         * 提供用户受保护路由的固定响应
         * @return 用于断言授权通过的响应标记
         */
        @GetMapping("/api/client/private")
        String privateClient() {
            return "private";
        }

        /**
         * 提供管理员受保护路由的固定响应
         * @return 用于断言授权通过的响应标记
         */
        @GetMapping("/api/admin/private")
        String privateAdmin() {
            return "admin";
        }
    }

    /** 验证匿名请求可访问公开路由 */
    @Test
    void anonymousCanUsePublicRoutes() throws Exception {
        assertThat(applicationContext.getBeansOfType(SecurityFilterChain.class)).hasSize(1);
        mvc.perform(post("/api/client/auth/login").contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk());
        mvc.perform(get("/api/client/subjects/1"))
                .andExpect(status().isOk());
        mvc.perform(post("/api/client/evidence/batch")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"subjectIds\":[1]}"))
                .andExpect(status().isOk());
        mvc.perform(post("/api/client/evidence/resolve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"entityType\":\"PERSON\",\"ids\":[1]}"))
                .andExpect(status().isOk());
        mvc.perform(get("/actuator/health"))
                .andExpect(status().isOk());
    }

    /** 验证匿名访问私有路由返回统一未认证响应 */
    @Test
    void anonymousPrivateRouteReturnsUnifiedUnauthorizedJson() throws Exception {
        mvc.perform(get("/api/client/private"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value(401));
    }

    /** 验证普通用户可访问用户端路由且不能访问管理端路由 */
    @Test
    void userCanUseClientRouteButNotAdminRoute() throws Exception {
        mvc.perform(get("/api/client/private").with(user("user").roles("USER")))
                .andExpect(status().isOk());
        mvc.perform(get("/api/admin/private").with(user("user").roles("USER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));
    }

    /** 验证管理员可访问管理端路由且未知路由默认拒绝 */
    @Test
    void adminCanUseAdminRouteButUnknownRouteIsDenied() throws Exception {
        mvc.perform(get("/api/admin/private").with(user("admin").roles("ADMIN")))
                .andExpect(status().isOk());
        mvc.perform(get("/unexpected").with(user("admin").roles("ADMIN")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));
    }
}
