package top.zhaizz.pojo.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 用户收藏条目视图（扁平化 JOIN 结果）
 */
@Data
public class UserCollectionSubjectVO {

    private Long id;            // 收藏ID
    private Long userId;        // 用户ID
    private Long subjectId;     // 条目ID
    private Integer type;       // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    private Integer rate;       // 评分（0~10, 0 表示未评分）
    private Integer epStatus;   // 看到第几集
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
    // subject 表的字段（扁平化 JOIN 结果）
    private String name;        // 日文/英文名
    private String nameCn;      // 中文名
    private String image;       // 封面图URL
    private BigDecimal score;   // Bangumi 评分
    private Integer eps;        // 总集数
    private LocalDate airDate;  // 播出日期
    private Integer airWeekday; // 播出星期
    private Integer subjectType;// 条目类型（2=动画）
}
