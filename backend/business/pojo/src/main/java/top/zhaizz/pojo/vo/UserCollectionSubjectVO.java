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

    private Long id;
    private Long userId;
    private Long subjectId;
    private Integer type;           // 收藏类型: 1=想看 2=看过 3=在看 4=搁置 5=抛弃
    private Integer rate;
    private Integer epStatus;       // 剧集进度
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    // subject 表的字段（扁平化 JOIN 结果）
    private String name;
    private String nameCn;
    private String image;
    private BigDecimal score;
    private Integer eps;
    private LocalDate airDate;
    private Integer subjectType;    // 条目类型
}
