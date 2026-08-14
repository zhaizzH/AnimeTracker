package top.zhaizz.client.util;

import com.resend.Resend;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 邮件发送客户端配置：装配 Resend SDK Bean，api-key 来自配置
 */
@Configuration
public class ResendConfig {

    /** 装配 Resend 邮件客户端（验证码/通知邮件均经此 Bean 发送） */
    @Bean
    public Resend resend(@Value("${resend.api-key}") String apiKey) {
        return new Resend(apiKey);
    }
}
