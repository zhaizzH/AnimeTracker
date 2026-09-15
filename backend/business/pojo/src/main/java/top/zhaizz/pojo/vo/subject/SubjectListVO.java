package top.zhaizz.pojo.vo.subject;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 条目列表视图（摘要信息）
 */
@Data
public class SubjectListVO {

    /** 条目ID */
    private Long id;            // 条目ID
    /** 日文/英文名 */
    private String name;        // 日文/英文名
    /** 中文名 */
    private String nameCn;      // 中文名
    /** 封面图URL */
    private String image;       // 封面图URL
    /** Bangumi 评分（0.0~10.0） */
    private BigDecimal score;   // Bangumi 评分（0.0~10.0）
    /** Bangumi 排名 */
    private Integer rank;       // Bangumi 排名
    /** 总集数 */
    private Integer eps;        // 总集数
    /** 播出日期 */
    private LocalDate airDate;  // 播出日期
    /** 条目类型（2=动画） */
    private Integer type;       // 条目类型（2=动画）
    /** 播出星期（0=周日, 1=周一 ... 6=周六） */
    private Integer airWeekday; // 播出星期（0=周日, 1=周一 ... 6=周六）
    /** 收藏数 */
    private Integer collectionTotal;    // 收藏数
}
