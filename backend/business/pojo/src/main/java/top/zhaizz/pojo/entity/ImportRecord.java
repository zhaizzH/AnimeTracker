package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;
/**
 * 导入记录实体
 */
@Data
@TableName("import_record")
public class ImportRecord {
    private Long id;
    private String mode;            // 导入模式（BANGUMI）
    private String seasonKey;       // 季度标识，如 "2026-spring"
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private String status;          // RUNNING / COMPLETED / FAILED
    private int subjectCount;
    private String errorMessage;
    private LocalDateTime createdAt;
}
