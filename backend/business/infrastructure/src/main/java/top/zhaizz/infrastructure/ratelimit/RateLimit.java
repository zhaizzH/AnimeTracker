package top.zhaizz.infrastructure.ratelimit;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** 方法级限流规则，所有可解析的规则必须全部通过 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RateLimit {
    /** 限流桶的请求维度 */
    enum LimitKey {
        /** 从第一个提供有效 getEmail 返回值的参数读取邮箱 */
        EMAIL,
        /** 使用 HTTP 请求的 remoteAddr，不读取代理转发头 */
        IP
    }

    /** 一条独立计数的限流约束 */
    @interface Rule {
        /**
         * 指定桶的请求维度
         * @return 邮箱或来源 IP 维度
         */
        LimitKey key();
        /**
         * 指定窗口内最大尝试次数
         * @return 最大允许次数
         */
        int limit();
        /**
         * 指定首次计数时的有效期
         * @return 窗口长度，单位秒
         */
        int windowSeconds();
    }

    /**
     * 返回按声明顺序执行的规则
     * @return 必须全部通过的规则数组；无法解析桶的规则跳过
     */
    Rule[] value();
}
