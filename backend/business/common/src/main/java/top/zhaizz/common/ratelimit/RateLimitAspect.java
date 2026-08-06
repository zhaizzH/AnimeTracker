package top.zhaizz.common.ratelimit;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.exception.BizException;

import java.lang.reflect.Method;

@Aspect
@Component
@RequiredArgsConstructor
public class RateLimitAspect {

    private final RateLimiter rateLimiter;

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

    /** 解析限流桶：EMAIL 从参数 DTO 反射取 email；IP 取请求来源。解析不到则跳过该条规则 */
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
