package top.zhaizz.common.config;

import org.slf4j.MDC;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.constant.TraceConstants;

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
                // Business → Agent 转发同一请求级 traceId
                .additionalInterceptors(traceForwardingInterceptor())
                .build();
    }

    /** 把当前请求 MDC 中的 traceId 透传给下游（Agent） */
    @Bean
    public ClientHttpRequestInterceptor traceForwardingInterceptor() {
        return (request, body, execution) -> {
            String traceId = MDC.get(TraceConstants.MDC_TRACE_ID);
            if (traceId != null) {
                request.getHeaders().set(TraceConstants.HEADER_X_REQUEST_ID, traceId);
            }
            return execution.execute(request, body);
        };
    }
}
