package top.zhaizz.client.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 收藏进度候选项（聚合查询结果，非 HTTP 返回体）
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CollectionProgressCandidate {

    private Long subjectId;             // 条目ID
    private String subjectName;         // 条目名称
    private Integer currentEpStatus;    // 当前进度
    private Integer targetEpStatus;     // 目标进度（本周区间内已播本篇最大整数集数）
    private Integer totalEpisodes;      // 总集数
}
