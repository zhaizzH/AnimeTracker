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
import top.zhaizz.common.security.JwtAuthenticationFilter;
import org.springframework.security.web.SecurityFilterChain;

import static org.assertj.core.api.Assertions.assertThat;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = SecurityConfigAuthorizationTest.TestController.class)
@Import({SecurityConfig.class, CorsConfig.class})
@ContextConfiguration(classes = SecurityConfigAuthorizationTest.TestConfig.class)
@TestPropertySource(properties = "at.cors.allowed-origins[0]=http://allowed.test")
class SecurityConfigAuthorizationTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private ApplicationContext applicationContext;

    @SpringBootConfiguration
    static class TestApplication {
    }

    @TestConfiguration(proxyBeanMethods = false)
    static class TestConfig {
        @Bean
        TestController testController() {
            return new TestController();
        }

        @Bean
        JwtAuthenticationFilter jwtAuthenticationFilter() {
            return new JwtAuthenticationFilter(null, null);
        }

    }

    @RestController
    static class TestController {
        @PostMapping("/api/client/auth/login")
        String login() {
            return "login";
        }

        @GetMapping("/api/client/subjects/1")
        String publicSubject() {
            return "subject";
        }

        @GetMapping("/actuator/health")
        String health() {
            return "ok";
        }

        @PostMapping("/api/client/evidence/batch")
        String evidenceBatch() {
            return "evidence";
        }

        @PostMapping("/api/client/evidence/resolve")
        String evidenceResolve() {
            return "evidence";
        }

        @GetMapping("/api/client/private")
        String privateClient() {
            return "private";
        }

        @GetMapping("/api/admin/private")
        String privateAdmin() {
            return "admin";
        }
    }

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

    @Test
    void anonymousPrivateRouteReturnsUnifiedUnauthorizedJson() throws Exception {
        mvc.perform(get("/api/client/private"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value(401));
    }

    @Test
    void userCanUseClientRouteButNotAdminRoute() throws Exception {
        mvc.perform(get("/api/client/private").with(user("user").roles("USER")))
                .andExpect(status().isOk());
        mvc.perform(get("/api/admin/private").with(user("user").roles("USER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));
    }

    @Test
    void adminCanUseAdminRouteButUnknownRouteIsDenied() throws Exception {
        mvc.perform(get("/api/admin/private").with(user("admin").roles("ADMIN")))
                .andExpect(status().isOk());
        mvc.perform(get("/unexpected").with(user("admin").roles("ADMIN")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));
    }
}
