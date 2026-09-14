package top.zhaizz.app.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * MyBatis-Plus 插件配置（分页拦截器）。
 */
@Configuration
public class MyBatisPlusConfig {

    /**
     * 注册明确使用 MySQL 方言、单页最多 100 条的分页插件。
     *
     * @return 包含 MySQL 分页插件的拦截器链
     */
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        PaginationInnerInterceptor pagination = new PaginationInnerInterceptor(DbType.MYSQL);
        pagination.setMaxLimit(100L);  // 单页最大 100 条
        pagination.setOverflow(true);  // 超过最大页数时按插件策略回到第一页
        interceptor.addInnerInterceptor(pagination);
        return interceptor;
    }
}
