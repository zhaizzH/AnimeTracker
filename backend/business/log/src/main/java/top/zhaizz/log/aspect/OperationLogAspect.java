package top.zhaizz.log.aspect;

import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import org.springframework.web.servlet.HandlerMapping;
import top.zhaizz.auth.util.SecurityUtil;
import top.zhaizz.log.annotation.OperationLog;
import top.zhaizz.log.mapper.OperationLogMapper;

import java.time.LocalDateTime;

/** 采集动作、身份与耗时等审计元数据，不记录请求正文或原始异常消息。 */
@Aspect
@Component
@RequiredArgsConstructor
@Slf4j
public class OperationLogAspect {
    /** 操作日志存储入口，写入异常只产生安全告警。 */
    private final OperationLogMapper operationLogMapper;

    /**
     * 执行业务方法，并在成功或失败后旁路记录操作日志。
     * @param pjp 被增强的业务调用，不可为空
     * @param annotation 声明的动作与模块编码，不可为空
     * @return 原业务返回值，允许为空
     * @throws Throwable 原业务抛出的同一个异常，不被日志失败替换
     */
    @Around("@annotation(annotation)")
    public Object around(ProceedingJoinPoint pjp, OperationLog annotation) throws Throwable {
        long start = System.nanoTime();
        try {
            Object result = pjp.proceed();
            record(annotation, null, start);
            return result;
        } catch (Throwable failure) {
            record(annotation, failure, start);
            throw failure;
        }
    }

    /**
     * 保存安全的操作元数据；参数、用户名输入和异常原文不进入日志。
     * @param annotation 操作注解，不可为空
     * @param failure 原业务异常；成功时为空
     * @param start 单调时钟的开始纳秒数
     */
    private void record(OperationLog annotation, Throwable failure, long start) {
        try {
            top.zhaizz.pojo.entity.OperationLog entity = new top.zhaizz.pojo.entity.OperationLog();
            entity.setAction(annotation.action());
            entity.setModule(annotation.module());
            entity.setStatus(failure == null ? 0 : 1);
            entity.setErrorMsg(failure == null ? null : failure.getClass().getSimpleName());
            entity.setDurationMs((System.nanoTime() - start) / 1_000_000);
            entity.setCreatedAt(LocalDateTime.now());
            entity.setUserId(SecurityUtil.getCurrentUserIdQuietly());
            HttpServletRequest request = currentRequest();
            if (request != null) {
                entity.setMethod(request.getMethod());
                Object pattern = request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
                entity.setPath(pattern instanceof String route ? route : null);
                entity.setIp(request.getRemoteAddr());
            }
            operationLogMapper.insert(entity);
        } catch (Exception failureToRecord) {
            log.warn("操作日志写入失败，异常类型={}", failureToRecord.getClass().getSimpleName());
        }
    }

    /**
     * 获取当前线程绑定的 HTTP 请求。
     * @return 当前请求；非 HTTP 调用时为空
     */
    private HttpServletRequest currentRequest() {
        var attrs = RequestContextHolder.getRequestAttributes();
        return attrs instanceof ServletRequestAttributes servlet ? servlet.getRequest() : null;
    }
}
