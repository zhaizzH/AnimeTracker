package top.zhaizz.app;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * AnimeTracker 应用入口
 */
@SpringBootApplication(scanBasePackages = "top.zhaizz")
@MapperScan("top.zhaizz.**.mapper")
@EnableScheduling
public class AppApplication {

    public static void main(String[] args) {
        SpringApplication.run(AppApplication.class, args);
    }
}
