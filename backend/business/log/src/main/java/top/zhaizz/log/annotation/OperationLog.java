package top.zhaizz.log.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** 标记需要采集操作审计日志的接口方法，采集失败不影响业务结果 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface OperationLog {
    /**
     * 指定本次操作的稳定动作编码
     * @return 与管理端筛选一致的动作编码
     */
    String action();
    /**
     * 指定本次操作所属的业务模块
     * @return 与管理端筛选一致的模块编码
     */
    String module();
}
