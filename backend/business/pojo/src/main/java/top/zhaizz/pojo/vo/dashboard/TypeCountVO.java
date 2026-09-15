package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 收藏类型分布
 */
@Data
public class TypeCountVO {
    /** 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃 */
    private Integer type;   // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    /** 该类型数量 */
    private long count;     // 该类型数量
}
