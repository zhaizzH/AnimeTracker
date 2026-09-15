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

    /** 条目ID */
    private Long subjectId;             // 条目ID
    /** 条目名称 */
    private String subjectName;         // 条目名称
    /** 当前进度 */
    private Integer currentEpStatus;    // 当前进度
    /** 目标进度（本周区间内已播本篇最大整数集数） */
    private Integer targetEpStatus;     // 目标进度（本周区间内已播本篇最大整数集数）
    /** 总集数 */
    private Integer totalEpisodes;      // 总集数
}
