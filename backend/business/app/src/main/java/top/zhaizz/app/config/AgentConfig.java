package top.zhaizz.app.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.MDC;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.agent.service.impl.AgentServiceImpl;
import top.zhaizz.common.constant.TraceConstants;

import java.time.Duration;

/**
 * Agent HTTP 客户端与服务装配：连接/读超时取自 at.agent.*。
 */
@Configuration
@EnableConfigurationProperties(AgentProperties.class)
public class AgentConfig {

    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder, AgentProperties agentProperties) {
        return builder
                .setConnectTimeout(Duration.ofMillis(agentProperties.getConnectTimeout()))
                .setReadTimeout(Duration.ofMillis(agentProperties.getReadTimeout()))
                // Business → Agent 转发同一请求级 traceId
                .additionalInterceptors(traceForwardingInterceptor())
                .build();
    }

    /** 由应用装配层注入 Agent 运行时配置，避免 agent 模块反向依赖 app。 */
    @Bean
    public AgentService agentService(RestTemplate restTemplate, AgentProperties agentProperties,
                                    ObjectMapper objectMapper) {
        return new AgentServiceImpl(restTemplate, objectMapper, agentProperties.getBaseUrl(),
                agentProperties.getConnectTimeout());
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
