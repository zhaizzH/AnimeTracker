package top.zhaizz.common.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import lombok.Data;

@Data
@ConfigurationProperties(prefix = "at.agent")
public class AgentProperties {
    /** Agent 服务地址 */
    private String baseUrl;
}
