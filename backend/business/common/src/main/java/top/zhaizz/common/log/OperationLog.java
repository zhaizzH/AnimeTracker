package top.zhaizz.common.log;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 操作日志注解：标注在需要记录日志的 Controller 方法上
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface OperationLog {
    String action();   // 如 LOGIN / SUBJECT_CREATE / IMPORT_RUN
    String module();   // 如 AUTH / SUBJECT / IMPORT
}
