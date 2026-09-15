package top.zhaizz.pojo.vo.imprt;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 导入记录 VO
 */
@Data
public class ImportRecordVO {

    /** 记录ID */
    private Long id;                    // 记录ID
    /** 季度标识（如 2026-spring） */
    private String season;              // 季度标识（如 2026-spring）
    /** 开始时间 */
    private LocalDateTime startedAt;    // 开始时间
    /** 完成时间（可空） */
    private LocalDateTime completedAt;  // 完成时间（可空）
    /** 状态: RUNNING, COMPLETED, FAILED */
    private String status;              // 状态: RUNNING, COMPLETED, FAILED
    /** 本次导入的条目数 */
    private Integer subjectCount;       // 本次导入的条目数
    /** 错误信息（失败时记录） */
    private String errorMessage;        // 错误信息（失败时记录）
}
