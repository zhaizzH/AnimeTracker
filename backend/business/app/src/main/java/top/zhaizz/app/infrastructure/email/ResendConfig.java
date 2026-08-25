package top.zhaizz.app.infrastructure.email;

import com.resend.Resend;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** 装配 Resend SDK 客户端。 */
@Configuration
public class ResendConfig {
    @Bean
    public Resend resend(@Value("${resend.api-key}") String apiKey) {
        return new Resend(apiKey);
    }
}
