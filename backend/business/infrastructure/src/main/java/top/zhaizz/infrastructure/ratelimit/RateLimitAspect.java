package top.zhaizz.infrastructure.ratelimit;

import lombok.RequiredArgsConstructor;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;

import java.lang.reflect.Method;

/**
 * 限流切面：@RateLimit 各规则逐条校验，超限抛 429。
 */
@Aspect
@Component
@RequiredArgsConstructor
public class RateLimitAspect {

    /** 逐条规则计数与配额判断入口。 */
    private final RateLimiter rateLimiter;

    /**
     * 依次计数所有可解析规则，全部通过后调用业务方法。
     * @param pjp 被增强的业务调用
     * @param rateLimit 方法声明的限流规则
     * @return 业务方法的原始返回值
     * @throws Throwable 超限时抛出 TOO_MANY_REQUESTS 业务异常；其他异常原样传播
     */
    @Around("@annotation(rateLimit)")
    public Object around(ProceedingJoinPoint pjp, RateLimit rateLimit) throws Throwable {
        for (RateLimit.Rule rule : rateLimit.value()) {
            String bucket = resolveBucket(rule.key(), pjp.getArgs());
            if (bucket != null && !rateLimiter.allowOrCount(bucket, rule.limit(), rule.windowSeconds())) {
                throw new BizException(ErrorType.TOO_MANY_REQUESTS, "请求过于频繁，请稍后再试");
            }
        }
        return pjp.proceed();
    }

    /**
     * 从请求参数邮箱或 HTTP 来源地址解析桶标识。
     * @param key 桶维度
     * @param args 业务方法参数，元素可为 null
     * @return 带维度前缀的桶后缀；缺少可用数据时返回 null，跳过该规则
     */
    private String resolveBucket(RateLimit.LimitKey key, Object[] args) {
        if (key == RateLimit.LimitKey.EMAIL) {
            for (Object arg : args) {
                if (arg == null) continue;
                try {
                    Method m = arg.getClass().getMethod("getEmail");
                    Object value = m.invoke(arg);
                    if (value instanceof String s && !s.isBlank()) return "email:" + s;
                } catch (Exception ignored) {
                }
            }
            return null;
        }
        var attrs = RequestContextHolder.getRequestAttributes();
        if (attrs instanceof ServletRequestAttributes sra) {
            return "ip:" + sra.getRequest().getRemoteAddr();
        }
        return null;
    }
}
