package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 通用搜索索引任务实体。
 */
@Data
@TableName("search_index_job")
public class SearchIndexJob {

    /** 索引任务ID。 */
    private Long id;                        // 索引任务ID
    /** 实体类型: SUBJECT/EPISODE/PERSON/CHARACTER。 */
    private String entityKind;              // 实体类型: SUBJECT/EPISODE/PERSON/CHARACTER
    /** 本地实体ID。 */
    private Long entityId;                  // 本地实体ID
    /** 索引版本。 */
    private String indexVersion;            // 索引版本
    /** 档案模板版本。 */
    private String profileVersion;          // 档案模板版本
    /** 档案内容哈希。 */
    private String contentHash;             // 档案内容哈希
    /** Embedding 供应商。 */
    private String embeddingProvider;       // Embedding 供应商
    /** Embedding 模型。 */
    private String embeddingModel;          // Embedding 模型
    /** 向量维度。 */
    private Integer embeddingDimensions;    // 向量维度
    /** 任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE。 */
    private String status;                  // 任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE
    /** 尝试次数。 */
    private Integer attempts;               // 尝试次数
    /** 最大尝试次数。 */
    private Integer maxAttempts;            // 最大尝试次数
    /** 最近错误码。 */
    private String lastErrorCode;           // 最近错误码
    /** 脱敏后的最近错误信息。 */
    private String lastErrorMessage;        // 脱敏后的最近错误信息
    /** 下次重试时间。 */
    private LocalDateTime nextRetryAt;      // 下次重试时间
    /** 认领时间。 */
    private LocalDateTime claimedAt;        // 认领时间
    /** 完成索引时间。 */
    private LocalDateTime indexedAt;        // 完成索引时间
    /** 创建时间。 */
    private LocalDateTime createdAt;        // 创建时间
    /** 更新时间。 */
    private LocalDateTime updatedAt;        // 更新时间
}
