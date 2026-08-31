package top.zhaizz.app.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.common.security.CookieOriginFilter;

import static org.assertj.core.api.Assertions.assertThat;

class AppConfigurationBindingTest {

    private final ApplicationContextRunner contextRunner = new ApplicationContextRunner()
            .withUserConfiguration(
                    AgentConfig.class,
                    CorsConfig.class)
            .withBean(RestTemplateBuilder.class, RestTemplateBuilder::new)
            .withBean(ObjectMapper.class, ObjectMapper::new)
            .withPropertyValues(
                    "at.agent.base-url=http://agent.test",
                    "at.agent.connect-timeout=1200",
                    "at.agent.read-timeout=3400",
                    "at.cors.allowed-origins[0]=http://allowed.test");

    @Test
    void bindsPropertiesAndBuildsExpectedCorsAndHttpBeans() {
        contextRunner.run(context -> {
            assertThat(context).hasSingleBean(AgentProperties.class);
            assertThat(context).hasSingleBean(CorsProperties.class);
            assertThat(context).hasSingleBean(RestTemplate.class);
            assertThat(context).hasSingleBean(AgentService.class);
            assertThat(context).hasSingleBean(ClientHttpRequestInterceptor.class);
            assertThat(context).hasSingleBean(CorsConfigurationSource.class);
            assertThat(context).hasSingleBean(CookieOriginFilter.class);

            AgentProperties agent = context.getBean(AgentProperties.class);
            assertThat(agent.getBaseUrl()).isEqualTo("http://agent.test");
            assertThat(agent.getConnectTimeout()).isEqualTo(1200);
            assertThat(agent.getReadTimeout()).isEqualTo(3400);

            MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/test");
            CorsConfiguration cors = context.getBean(CorsConfigurationSource.class)
                    .getCorsConfiguration(request);
            assertThat(cors).isNotNull();
            assertThat(cors.getAllowedOrigins()).containsExactly("http://allowed.test");
            assertThat(cors.getAllowedMethods()).containsExactly("GET", "POST", "OPTIONS");
            assertThat(cors.getAllowedHeaders())
                    .containsExactly("Authorization", "Content-Type", "X-Request-ID");
            assertThat(cors.getAllowCredentials()).isTrue();
        });
    }
}
