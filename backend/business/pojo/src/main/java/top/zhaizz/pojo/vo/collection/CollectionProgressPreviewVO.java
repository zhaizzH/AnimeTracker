package top.zhaizz.pojo.vo.collection;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 本周追番进度预览返回体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CollectionProgressPreviewVO {

    private String previewId;                   // 预览ID
    private CollectionProgressState state;      // 预览状态
    private OffsetDateTime expiresAt;           // 过期时间
    private LocalDate weekStart;                // 本周周一
    private LocalDate cutoffDate;               // 截止日期（昨日）
    @Builder.Default
    private List<CollectionProgressItemVO> items = new ArrayList<>();
}
