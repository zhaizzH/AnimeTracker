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
    private String mode;
    private String seasonKey;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private String status;
    private int subjectCount;
    private String errorMessage;
    private LocalDateTime createdAt;
}
