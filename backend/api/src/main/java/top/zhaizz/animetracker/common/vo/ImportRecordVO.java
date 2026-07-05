package top.zhaizz.animetracker.common.vo;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 导入记录 VO
 */
@Data
public class ImportRecordVO {

    private Long id;
    private String season;          // 如 "2026-spring"
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;  // 可空
    private String status;          // RUNNING / COMPLETED / FAILED
    private Integer subjectCount;
    private String errorMessage;    // 可空
}
