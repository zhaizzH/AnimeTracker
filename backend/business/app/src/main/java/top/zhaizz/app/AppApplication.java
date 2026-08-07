package top.zhaizz.app;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * AnimeTracker 应用入口
 * <p>
 * 扫描 top.zhaizz 包下组件,注册 MyBatis mapper 并开启定时任务调度
 */
@SpringBootApplication(scanBasePackages = "top.zhaizz")
@MapperScan("top.zhaizz.**.mapper")
@EnableScheduling
public class AppApplication {

    public static void main(String[] args) {
        SpringApplication.run(AppApplication.class, args);
    }
}
