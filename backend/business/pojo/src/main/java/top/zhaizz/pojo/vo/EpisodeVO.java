package top.zhaizz.pojo.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 剧集信息 VO
 */
@Data
public class EpisodeVO {

    private Long id;
    private Long subjectId;
    private Integer type;           // 0=本篇 1=SP 2=OP 3=ED 4=预告
    private BigDecimal sort;
    private String name;
    private String nameCn;
    private String duration;
    private LocalDate airdate;
    private String description;
    private String status;          // Air / Today / NA
}
