package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 操作/登录日志实体
 */
@Data
@TableName("operation_log")
public class OperationLogEntity {
    private Long id;
    private Long userId;
    private String username;
    private String action;
    private String module;
    private String method;
    private String path;
    private String params;
    private String ip;
    private String userAgent;
    private Integer status;   // 0=成功, 1=失败
    private String errorMsg;
    private Long durationMs;
    private LocalDateTime createdAt;
}
