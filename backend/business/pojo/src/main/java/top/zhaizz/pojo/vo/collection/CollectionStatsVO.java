package top.zhaizz.pojo.vo.collection;

import lombok.Data;
import top.zhaizz.pojo.vo.RatingCountVO;
import top.zhaizz.pojo.vo.TypeCountVO;

import java.util.List;

/**
 * 收藏统计 VO
 */
@Data
public class CollectionStatsVO {
    private List<TypeCountVO> types;        // 各收藏类型数量分布
    private List<RatingCountVO> ratings;    // 各评分数量分布
}
