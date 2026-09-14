package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 实体详情渐进回填任务实体。
 */
@Data
@TableName("entity_detail_job")
public class EntityDetailJob {

    /** 任务ID。 */
    private Long id;                        // 任务ID
    /** 实体类型: PERSON/CHARACTER。 */
    private String entityKind;              // 实体类型: PERSON/CHARACTER
    /** 本地实体ID。 */
    private Long entityId;                  // 本地实体ID
    /** Bangumi 上游ID。 */
    private Integer sourceId;               // Bangumi 上游ID
    /** 任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED。 */
    private String status;                  // 任务状态: PENDING/CLAIMED/RUNNING/COMPLETED/FAILED/ABANDONED
    /** 尝试次数。 */
    private Integer attempts;               // 尝试次数
    /** 最大尝试次数。 */
    private Integer maxAttempts;            // 最大尝试次数
    /** 下次重试时间。 */
    private LocalDateTime nextRetryAt;      // 下次重试时间
    /** 最近错误码。 */
    private String lastErrorCode;           // 最近错误码
    /** 脱敏后的最近错误信息。 */
    private String lastErrorMessage;        // 脱敏后的最近错误信息
    /** 回填断点 JSON。 */
    private String checkpointJson;          // 回填断点 JSON
    /** 完成时的来源数据哈希。 */
    private String sourceHash;              // 完成时的来源数据哈希
    /** 认领时间。 */
    private LocalDateTime claimedAt;        // 认领时间
    /** 完成时间。 */
    private LocalDateTime completedAt;      // 完成时间
    /** 创建时间。 */
    private LocalDateTime createdAt;        // 创建时间
    /** 更新时间。 */
    private LocalDateTime updatedAt;        // 更新时间
}
