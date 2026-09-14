package top.zhaizz.infrastructure.email.resend;

import com.resend.Resend;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** 装配 Resend SDK 客户端。 */
@Configuration
public class ResendConfig {
    /**
     * 使用配置密钥创建邮件 SDK 客户端。
     * @param apiKey resend.api-key 配置的密钥，不得记录到日志
     * @return 邮件发送客户端
     */
    @Bean
    public Resend resend(@Value("${resend.api-key}") String apiKey) {
        return new Resend(apiKey);
    }
}
