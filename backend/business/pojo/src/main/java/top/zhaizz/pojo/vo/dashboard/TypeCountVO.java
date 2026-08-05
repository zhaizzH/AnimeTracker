package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 收藏类型分布
 */
@Data
public class TypeCountVO {
    private Integer type;   // 1=想看, 2=在看, 3=看过, 4=搁置, 5=抛弃
    private long count;
}
