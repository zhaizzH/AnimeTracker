package top.zhaizz.pojo.vo.collection;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 收藏进度预览/执行明细项
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CollectionProgressItemVO {

    /** 条目ID */
    private Long subjectId;                 // 条目ID
    /** 条目名称 */
    private String subjectName;             // 条目名称
    /** 当前进度 */
    private Integer currentEpStatus;        // 当前进度
    /** 目标进度 */
    private Integer targetEpStatus;         // 目标进度
    /** 更新后是否达到总集数 */
    private boolean completedAfterUpdate;   // 更新后是否达到总集数
    /** 是否建议标记为看过 */
    private boolean suggestMarkAsWatched;   // 是否建议标记为看过
}
