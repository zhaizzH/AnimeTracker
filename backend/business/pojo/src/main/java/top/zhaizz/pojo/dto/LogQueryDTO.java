package top.zhaizz.pojo.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

/**
 * 日志查询参数
 */
@Data
public class LogQueryDTO {

    private String action;      // 动作
    private String module;      // 模块
    private String username;    // 用户名/邮箱快照
    private Long userId;        // 用户ID
    private Integer status;     // 状态: 0=成功, 1=失败
    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
    private LocalDate start;    // 开始日期(含)
    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
    private LocalDate end;      // 结束日期(含)
    @Min(1)
    private int page = 1;       // 页码
    @Min(1)
    @Max(100)
    private int size = 20;      // 每页条数
}
