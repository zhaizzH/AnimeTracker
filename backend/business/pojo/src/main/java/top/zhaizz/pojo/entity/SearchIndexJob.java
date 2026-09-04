package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 通用搜索索引任务实体
 */
@Data
@TableName("search_index_job")
public class SearchIndexJob {

    private Long id;                        // 索引任务ID
    private String entityKind;              // 实体类型: SUBJECT/EPISODE/PERSON/CHARACTER
    private Long entityId;                  // 本地实体ID
    private String indexVersion;            // 索引版本
    private String profileVersion;          // 档案模板版本
    private String contentHash;             // 档案内容哈希
    private String embeddingProvider;       // Embedding 供应商
    private String embeddingModel;          // Embedding 模型
    private Integer embeddingDimensions;    // 向量维度
    private String status;                  // 任务状态: PENDING/CLAIMED/COMPLETED/FAILED/TOMBSTONE
    private Integer attempts;               // 尝试次数
    private Integer maxAttempts;            // 最大尝试次数
    private String lastErrorCode;           // 最近错误码
    private String lastErrorMessage;        // 脱敏后的最近错误信息
    private LocalDateTime nextRetryAt;      // 下次重试时间
    private LocalDateTime claimedAt;        // 认领时间
    private LocalDateTime indexedAt;        // 完成索引时间
    private LocalDateTime createdAt;        // 创建时间
    private LocalDateTime updatedAt;        // 更新时间
}
