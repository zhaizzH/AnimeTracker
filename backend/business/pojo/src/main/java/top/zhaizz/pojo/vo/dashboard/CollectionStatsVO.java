package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.util.List;

/**
 * 收藏统计 VO
 */
@Data
public class CollectionStatsVO {
    private List<TypeCountVO> types;
    private List<RatingCountVO> ratings;
}
