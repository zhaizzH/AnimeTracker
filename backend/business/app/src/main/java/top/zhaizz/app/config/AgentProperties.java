package top.zhaizz.app.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import lombok.Data;

/**
 * LLM Agent 服务连接配置
 */
@Data
@ConfigurationProperties(prefix = "at.agent")
public class AgentProperties {
    /** Agent 服务地址 */
    private String baseUrl;
    /** 连接超时（毫秒） */
    private long connectTimeout = 10_000;
    /** 普通请求读超时（毫秒） */
    private long readTimeout = 30_000;
}
