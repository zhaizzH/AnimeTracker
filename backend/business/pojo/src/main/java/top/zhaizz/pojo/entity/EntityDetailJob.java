package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 实体详情渐进回填任务实体
 */
@Data
@TableName("entity_detail_job")
public class EntityDetailJob {

    private Long id;                        // 任务ID
    private String entityKind;              // 实体类型: PERSON/CHARACTER
    private Long entityId;                  // 本地实体ID
    private Integer sourceId;               // Bangumi 上游ID
    private String status;                  // 任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED
    private Integer attempts;               // 尝试次数
    private Integer maxAttempts;            // 最大尝试次数
    private LocalDateTime nextRetryAt;      // 下次重试时间
    private String lastErrorCode;           // 最近错误码
    private String lastErrorMessage;        // 脱敏后的最近错误信息
    private String checkpointJson;          // 回填断点 JSON
    private String sourceHash;              // 完成时的来源数据哈希
    private LocalDateTime claimedAt;        // 认领时间
    private LocalDateTime completedAt;      // 完成时间
    private LocalDateTime createdAt;        // 创建时间
    private LocalDateTime updatedAt;        // 更新时间
}
