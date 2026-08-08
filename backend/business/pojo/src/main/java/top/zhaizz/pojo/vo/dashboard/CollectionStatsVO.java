package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.util.List;

/**
 * 收藏统计 VO
 */
@Data
public class CollectionStatsVO {
    private List<TypeCountVO> types;        // 各收藏类型数量分布
    private List<RatingCountVO> ratings;    // 各评分数量分布
}
