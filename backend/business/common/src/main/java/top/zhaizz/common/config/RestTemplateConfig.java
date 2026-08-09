package top.zhaizz.common.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

/**
 * RestTemplate 配置：调用 Agent 服务用，连接/读超时取自 at.agent.*
 */
@Configuration
@EnableConfigurationProperties(AgentProperties.class)
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder, AgentProperties agentProperties) {
        return builder
                .setConnectTimeout(Duration.ofMillis(agentProperties.getConnectTimeout()))
                .setReadTimeout(Duration.ofMillis(agentProperties.getReadTimeout()))
                .build();
    }
}
