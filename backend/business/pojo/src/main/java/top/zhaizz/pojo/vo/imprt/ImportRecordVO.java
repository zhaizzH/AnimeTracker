package top.zhaizz.pojo.vo.imprt;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 导入记录 VO
 */
@Data
public class ImportRecordVO {

    private Long id;                    // 记录ID
    private String season;              // 季度标识（如 2026-spring）
    private LocalDateTime startedAt;    // 开始时间
    private LocalDateTime completedAt;  // 完成时间（可空）
    private String status;              // 状态: RUNNING, COMPLETED, FAILED
    private Integer subjectCount;       // 本次导入的条目数
    private String errorMessage;        // 错误信息（失败时记录）
}
