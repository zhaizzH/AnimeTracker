package top.zhaizz.animetracker;

import lombok.extern.slf4j.Slf4j;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.core.env.ConfigurableEnvironment;

import java.net.InetAddress;
import java.net.UnknownHostException;

/**
 * AnimeTracker API — Spring Boot 3.2 应用入口
 */
@Slf4j
@SpringBootApplication
public class AppApplication {

    public static void main(String[] args) {
        ConfigurableEnvironment env = SpringApplication.run(AppApplication.class, args).getEnvironment();

        String property = env.getProperty("spring.application.name");
        String hostAddress;  // 获取主机地址
        try {
            hostAddress = InetAddress.getLocalHost().getHostAddress();
        } catch (UnknownHostException e) {
            hostAddress = "127.0.0.1";
            log.warn("无法获取主机IP,使用默认地址: 127.0.0.1");
        }
        String serverPort = env.getProperty("server.port");

        log.info("""
                        \r----------------------------------------------------------
                        Application '{}' is running Success!
                        接口文档访问地址:
                        本地Knife4j地址:   http://localhost:{}/doc.html
                        外部Swagger地址:   http://{}:{}/swagger-ui/index.html
                        配置文件:   {}
                        ----------------------------------------------------------""",
                property,
                serverPort,
                hostAddress, serverPort,
                env.getActiveProfiles());
    }
}
