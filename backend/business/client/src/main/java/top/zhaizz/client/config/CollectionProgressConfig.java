package top.zhaizz.client.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Clock;
import java.time.ZoneId;

/**
 * 收藏进度业务时间源配置（时区固定 Asia/Shanghai）
 */
@Configuration
public class CollectionProgressConfig {

    /** 收藏进度计算统一时钟 */
    @Bean
    public Clock collectionProgressClock() {
        return Clock.system(ZoneId.of("Asia/Shanghai"));
    }
}
