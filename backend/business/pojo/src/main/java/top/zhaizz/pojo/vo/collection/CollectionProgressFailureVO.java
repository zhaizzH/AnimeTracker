package top.zhaizz.pojo.vo.collection;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 收藏进度执行跳过/失败项
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CollectionProgressFailureVO {

    private Long subjectId;                 // 条目ID
    private String subjectName;             // 条目名称
    private Integer currentEpStatus;        // 当前进度
    private Integer targetEpStatus;         // 目标进度
    private String reason;                  // 跳过/失败原因
}
