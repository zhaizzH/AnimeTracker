package top.zhaizz.client.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 收藏进度预览 Redis 快照（内部存储，永不直接作为 HTTP 返回）
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProgressPreviewSnapshot {

    private String previewId;                           // 预览ID
    private Long userId;                                // 用户ID
    private ProgressPreviewStatus status;               // 快照状态
    private LocalDate weekStart;                        // 本周周一
    private LocalDate cutoffDate;                       // 截止日期（昨日）
    @Builder.Default
    private List<CollectionProgressItemVO> items = new ArrayList<>();
    private OffsetDateTime createdAt;                   // 创建时间
    private OffsetDateTime expiresAt;                   // 过期时间
    private CollectionProgressExecutionVO executionResult; // 执行结果（COMPLETED 后用于幂等重放）
}
