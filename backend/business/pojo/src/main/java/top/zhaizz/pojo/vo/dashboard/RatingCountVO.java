package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 评分分布
 */
@Data
public class RatingCountVO {
    private Integer rate;   // 评分值 1~10
    private long count;     // 该评分数量
}
