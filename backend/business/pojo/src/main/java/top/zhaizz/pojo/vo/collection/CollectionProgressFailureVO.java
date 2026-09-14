package top.zhaizz.pojo.vo.collection;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 收藏进度执行跳过/失败项。
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CollectionProgressFailureVO {

    /** 条目ID。 */
    private Long subjectId;                 // 条目ID
    /** 条目名称。 */
    private String subjectName;             // 条目名称
    /** 当前进度。 */
    private Integer currentEpStatus;        // 当前进度
    /** 目标进度。 */
    private Integer targetEpStatus;         // 目标进度
    /** 跳过/失败原因。 */
    private String reason;                  // 跳过/失败原因
}
