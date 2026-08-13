package top.zhaizz.pojo.vo.log;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 操作日志 VO
 */
@Data
public class OperationLogVO {
    private Long id;            // 日志ID
    private Long userId;        // 用户ID（匿名失败登录为NULL）
    private String username;    // 用户名/邮箱快照
    private String action;      // 动作
    private String module;      // 模块
    private String method;      // HTTP 方法
    private String path;        // 请求路径
    private String ip;          // 客户端 IP
    private String userAgent;   // User-Agent
    private Integer status;     // 0=成功, 1=失败
    private String errorMsg;    // 失败原因
    private Long durationMs;    // 耗时(毫秒)
    private LocalDateTime createdAt;    // 创建时间
}
