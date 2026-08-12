package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 操作/登录日志实体
 */
@Data
@TableName("operation_log")
public class OperationLog {
    private Long id;                    // 日志ID
    private Long userId;                // 用户ID（匿名失败登录为NULL）
    private String username;            // 用户名/邮箱快照
    private String action;              // 动作: LOGIN/LOGOUT/REGISTER/SUBJECT_CREATE/SUBJECT_UPDATE/SUBJECT_DELETE/ROLE_CHANGE/IMPORT_RUN
    private String module;              // 模块: AUTH/USER/SUBJECT/IMPORT/ADMIN
    private String method;              // HTTP 方法
    private String path;                // 请求路径
    private String params;              // 请求参数 JSON（脱敏）
    private String ip;                  // 客户端 IP
    private String userAgent;           // User-Agent
    private Integer status;             // 0=成功, 1=失败
    private String errorMsg;            // 失败原因
    private Long durationMs;            // 耗时(毫秒)
    private LocalDateTime createdAt;    // 创建时间
}
