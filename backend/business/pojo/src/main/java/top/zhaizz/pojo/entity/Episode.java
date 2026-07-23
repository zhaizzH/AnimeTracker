package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 剧集实体
 */
@Data
@TableName("episode")
public class Episode {

    private Long id;
    private Long subjectId;
    private Integer bangumiEpId;
    private Integer type;           // 0=本篇 1=SP 2=OP 3=ED 4=预告
    private BigDecimal sort;        // 排序序号
    private String name;
    private String nameCn;
    private String duration;
    private LocalDate airdate;
    private String description;
    private String status;          // Air / Today / NA
    private LocalDateTime createdAt;
}
