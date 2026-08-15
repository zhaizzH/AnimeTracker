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

    private Long subjectId;                 // 条目ID
    private String subjectName;             // 条目名称
    private Integer currentEpStatus;        // 当前进度
    private Integer targetEpStatus;         // 目标进度
    private boolean completedAfterUpdate;   // 更新后是否达到总集数
    private boolean suggestMarkAsWatched;   // 是否建议标记为看过
}
