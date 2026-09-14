package top.zhaizz.app.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.MDC;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.agent.gateway.HttpImportAgentGateway;
import top.zhaizz.agent.gateway.ImportAgentGateway;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.agent.service.impl.AgentServiceImpl;
import top.zhaizz.agent.constant.TraceConstants;

import java.time.Duration;

/**
 * Agent HTTP 客户端与服务装配：连接/读超时取自 at.agent.*。
 */
@Configuration
@EnableConfigurationProperties(AgentProperties.class)
public class AgentConfig {

    /**
     * 创建并配置 restTemplate Bean。
     *
     * @param builder Spring Boot HTTP 客户端构建器
     * @param agentProperties Agent 地址与以毫秒计的超时配置
     * @return 带超时限制和追踪头透传的普通 HTTP 客户端
     */
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder, AgentProperties agentProperties) {
        return builder
                .setConnectTimeout(Duration.ofMillis(agentProperties.getConnectTimeout()))
                .setReadTimeout(Duration.ofMillis(agentProperties.getReadTimeout()))
                // Business → Agent 转发同一请求级 traceId
                .additionalInterceptors(traceForwardingInterceptor())
                .build();
    }

    /**
     * 由应用装配层注入 Agent 运行时配置，避免 agent 模块反向依赖 app。
     *
     * @param restTemplate 已装配超时和请求追踪的普通 HTTP 客户端
     * @param agentProperties Agent 地址与以毫秒计的超时配置
     * @param objectMapper 应用共用的 JSON 序列化器
     * @return Agent HTTP 与 SSE 请求转发服务
     */
    @Bean
    public AgentService agentService(RestTemplate restTemplate, AgentProperties agentProperties,
                                    ObjectMapper objectMapper) {
        return new AgentServiceImpl(restTemplate, objectMapper, agentProperties.getBaseUrl(),
                agentProperties.getConnectTimeout());
    }

    /**
     * 由应用装配层注入导入网关，Agent 模块仅提供端口与 HTTP 实现。
     *
     * @param restTemplate 已装配超时和请求追踪的普通 HTTP 客户端
     * @param agentProperties Agent 地址与以毫秒计的超时配置
     * @return 导入任务 HTTP 通信入口
     */
    @Bean
    public ImportAgentGateway importAgentGateway(RestTemplate restTemplate, AgentProperties agentProperties) {
        return new HttpImportAgentGateway(restTemplate, agentProperties.getBaseUrl());
    }

    /**
     * 把当前请求 MDC 中的 traceId 透传给下游（Agent）。
     *
     * @return 追踪头拦截器，MDC 无追踪 ID 时不追加该头
     */
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
