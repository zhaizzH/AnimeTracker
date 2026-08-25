package top.zhaizz.app.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.test.context.junit.jupiter.web.SpringJUnitWebConfig;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.HandlerExecutionChain;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;
import top.zhaizz.admin.controller.AdminFileController;
import top.zhaizz.client.controller.ClientFileController;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.security.JwtAuthenticationFilter;
import top.zhaizz.common.security.JwtTokenProvider;
import top.zhaizz.common.storage.ImageCategory;
import top.zhaizz.common.storage.ImageStorageGateway;
import top.zhaizz.common.util.RedisUtil;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.reset;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringJUnitWebConfig(SecurityConfigAuthorizationTest.TestApp.class)
class SecurityConfigAuthorizationTest {

    @Autowired
    private WebApplicationContext webApplicationContext;

    @Autowired
    private ImageStorageGateway imageStorageGateway;

    @Autowired
    private RequestMappingHandlerMapping requestMappingHandlerMapping;

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        reset(imageStorageGateway);
        mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext)
                .apply(springSecurity())
                .build();
    }

    @Test
    void authenticatedUserCannotReachUnmatchedPath() throws Exception {
        mockMvc.perform(get("/api/unmatched").with(user("user").roles("USER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403))
                .andExpect(jsonPath("$.message").value("无权限"));
    }

    @Test
    void anonymousCanReadPublicSubjects() throws Exception {
        mockMvc.perform(get("/api/client/subjects/probe"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void anonymousCannotReachPrivateClientPath() throws Exception {
        mockMvc.perform(get("/api/client/probe"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value(401));
    }

    @Test
    void userCannotReachAdminPath() throws Exception {
        mockMvc.perform(get("/api/admin/probe").with(user("user").roles("USER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));
    }

    @Test
    void adminCanReachAdminPath() throws Exception {
        mockMvc.perform(get("/api/admin/probe").with(user("admin").roles("ADMIN")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void anonymousCannotUploadCover() throws Exception {
        mockMvc.perform(multipart("/api/admin/files/cover").file(pngFile()))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value(401));
    }

    @Test
    void anonymousCannotUploadAvatar() throws Exception {
        mockMvc.perform(multipart("/api/client/files/avatar").file(pngFile()))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value(401));
    }

    @Test
    void userCanUploadAvatar() throws Exception {
        when(imageStorageGateway.upload(any(), eq(ImageCategory.AVATAR)))
                .thenReturn("http://minio/anime/avatars/a.png");

        mockMvc.perform(multipart("/api/client/files/avatar")
                        .file(pngFile())
                        .with(user("user").roles("USER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data").value("http://minio/anime/avatars/a.png"));
    }

    @Test
    void adminCanUploadAvatar() throws Exception {
        when(imageStorageGateway.upload(any(), eq(ImageCategory.AVATAR)))
                .thenReturn("http://minio/anime/avatars/admin.png");

        mockMvc.perform(multipart("/api/client/files/avatar")
                        .file(pngFile())
                        .with(user("admin").roles("ADMIN")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data").value("http://minio/anime/avatars/admin.png"));

        verify(imageStorageGateway).upload(any(), eq(ImageCategory.AVATAR));
    }

    @Test
    void userCannotUploadCover() throws Exception {
        mockMvc.perform(multipart("/api/admin/files/cover")
                        .file(pngFile())
                        .with(user("user").roles("USER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));

        verifyNoInteractions(imageStorageGateway);
    }

    @Test
    void removedCommonUploadRouteHasNoHandlerMapping() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("POST", removedCommonUploadPath());

        HandlerExecutionChain handler = requestMappingHandlerMapping.getHandler(request);

        assertThat(handler).isNull();
    }

    @Test
    void adminCanUploadCover() throws Exception {
        when(imageStorageGateway.upload(any(), eq(ImageCategory.COVER)))
                .thenReturn("http://minio/anime/covers/c.png");

        mockMvc.perform(multipart("/api/admin/files/cover")
                        .file(pngFile())
                        .with(user("admin").roles("ADMIN")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data").value("http://minio/anime/covers/c.png"));
    }

    private MockMultipartFile pngFile() {
        return new MockMultipartFile("file", "image.png", "image/png", new byte[]{1});
    }

    private String removedCommonUploadPath() {
        return "/" + String.join("/", "api", "common", "files", "upload");
    }

    @Configuration
    @EnableWebMvc
    @Import({SecurityConfig.class, ClientFileController.class, AdminFileController.class,
            ProbeController.class, TestBeans.class})
    static class TestApp {
    }

    @Configuration
    static class TestBeans {
        @Bean
        JwtTokenProvider jwtTokenProvider() {
            return new JwtTokenProvider("01234567890123456789012345678901", 3600000L);
        }

        @Bean
        JwtAuthenticationFilter jwtAuthenticationFilter(JwtTokenProvider jwtTokenProvider) {
            return new JwtAuthenticationFilter(jwtTokenProvider, new RedisUtil());
        }

        @Bean
        CorsConfigurationSource corsConfigurationSource() {
            UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
            source.registerCorsConfiguration("/**", new CorsConfiguration());
            return source;
        }

        @Bean
        ObjectMapper objectMapper() {
            return new ObjectMapper();
        }

        @Bean
        ImageStorageGateway imageStorageGateway() {
            return Mockito.mock(ImageStorageGateway.class);
        }
    }

    @RestController
    static class ProbeController {
        @GetMapping("/api/unmatched")
        Result<Void> unmatched() {
            return Result.success();
        }

        @GetMapping("/api/client/probe")
        Result<Void> client() {
            return Result.success();
        }

        @GetMapping("/api/admin/probe")
        Result<Void> admin() {
            return Result.success();
        }

        @GetMapping("/api/client/subjects/probe")
        Result<Void> publicSubject() {
            return Result.success();
        }
    }
}
