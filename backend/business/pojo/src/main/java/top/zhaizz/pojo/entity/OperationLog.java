package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 操作/登录日志实体。
 */
@Data
@TableName("operation_log")
public class OperationLog {
    /** 日志ID。 */
    private Long id;
    /** 用户ID（匿名失败登录为NULL）。 */
    private Long userId;
    /** 用户名/邮箱快照。 */
    private String username;
    /** 动作: LOGIN/LOGOUT/REGISTER/SUBJECT_CREATE/SUBJECT_UPDATE/SUBJECT_DELETE/ROLE_CHANGE/IMPORT_RUN。 */
    private String action;
    /** 模块: AUTH/USER/SUBJECT/IMPORT/ADMIN。 */
    private String module;
    /** HTTP 方法。 */
    private String method;
    /** 请求路径。 */
    private String path;
    /** 历史请求参数字段，当前采集器不填充。 */
    private String params;
    /** 客户端 IP。 */
    private String ip;
    /** 客户端代理标识；当前采集器不填充，保留历史字段。 */
    private String userAgent;
    /** 0=成功, 1=失败。 */
    private Integer status;
    /** 失败原因。 */
    private String errorMsg;
    /** 耗时(毫秒)。 */
    private Long durationMs;
    /** 创建时间。 */
    private LocalDateTime createdAt;
}
