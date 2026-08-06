package top.zhaizz.common.ratelimit;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 方法级限流。多个 Rule 需全部通过（AND）。
 * EMAIL：从第一个含 getEmail() 的参数解析；IP：取请求 remoteAddr。
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RateLimit {

    enum LimitKey { EMAIL, IP }

    @interface Rule {
        LimitKey key();
        int limit();
        int windowSeconds();
    }

    Rule[] value();
}
