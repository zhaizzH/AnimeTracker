package top.zhaizz.common.log;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.common.util.SecurityUtil;

import java.lang.reflect.Method;
import java.time.LocalDateTime;

/**
 * 操作日志切面：@OperationLog 标注的方法统一采集日志，失败不影响业务
 */
@Aspect
@Component
@RequiredArgsConstructor
@Slf4j
public class OperationLogAspect {

    private final OperationLogMapper operationLogMapper;
    private final ObjectMapper objectMapper;

    /** 环绕增强：执行业务并记录操作日志，日志写入失败仅告警不阻断业务 */
    @Around("@annotation(annotation)")
    public Object around(ProceedingJoinPoint pjp, top.zhaizz.common.log.OperationLog annotation) throws Throwable {
        long start = System.currentTimeMillis();
        try {
            Object result = pjp.proceed();
            record(pjp, annotation, true, null, start);
            return result;
        } catch (Throwable t) {
            record(pjp, annotation, false, t.getMessage(), start);
            throw t;
        }
    }

    /** 组装日志实体（成功/失败状态、耗时、请求上下文）并入库 */
    private void record(ProceedingJoinPoint pjp, top.zhaizz.common.log.OperationLog ann, boolean success, String error, long start) {
        try {
            top.zhaizz.pojo.entity.OperationLog entity = new top.zhaizz.pojo.entity.OperationLog();
            entity.setAction(ann.action());
            entity.setModule(ann.module());
            entity.setStatus(success ? 0 : 1);
            entity.setErrorMsg(error);
            entity.setDurationMs(System.currentTimeMillis() - start);
            entity.setCreatedAt(LocalDateTime.now());
            entity.setUserId(SecurityUtil.getCurrentUserIdQuietly());
            entity.setUsername(resolveUsername(pjp.getArgs()));
            entity.setParams(toJson(pjp.getArgs()));
            HttpServletRequest request = currentRequest();
            if (request != null) {
                entity.setMethod(request.getMethod());
                entity.setPath(request.getRequestURI());
                entity.setIp(request.getRemoteAddr());
                entity.setUserAgent(request.getHeader("User-Agent"));
            }
            operationLogMapper.insert(entity);
        } catch (Exception e) {
            log.warn("操作日志写入失败: {}", e.getMessage());
        }
    }

    private HttpServletRequest currentRequest() {
        var attrs = RequestContextHolder.getRequestAttributes();
        return attrs instanceof ServletRequestAttributes sra ? sra.getRequest() : null;
    }

    /** 从请求体 DTO 反射提取 username/email（公开接口无 SecurityContext） */
    private String resolveUsername(Object[] args) {
        for (Object arg : args) {
            if (arg == null) continue;
            for (String getter : new String[]{"getUsername", "getEmail"}) {
                try {
                    Method m = arg.getClass().getMethod(getter);
                    Object value = m.invoke(arg);
                    if (value instanceof String s && !s.isBlank()) return s;
                } catch (Exception ignored) {
                }
            }
        }
        return null;
    }

    /** 参数 JSON 序列化并脱敏 password/code */
    private String toJson(Object[] args) {
        try {
            return objectMapper.writeValueAsString(args)
                    .replaceAll("(\"(password|oldPassword|newPassword|code)\"\\s*:\\s*)\"[^\"]*\"", "$1\"***\"");
        } catch (Exception e) {
            return null;
        }
    }
}
