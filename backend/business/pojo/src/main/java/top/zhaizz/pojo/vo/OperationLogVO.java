package top.zhaizz.pojo.vo;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 操作日志 VO
 */
@Data
public class OperationLogVO {
    private Long id;
    private Long userId;
    private String username;
    private String action;
    private String module;
    private String method;
    private String path;
    private String ip;
    private String userAgent;
    private Integer status;   // 0=成功, 1=失败
    private String errorMsg;
    private Long durationMs;
    private LocalDateTime createdAt;
}
