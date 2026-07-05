package top.zhaizz.animetracker.subject.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 动漫条目实体
 */
@Data
@TableName("subject")
public class Subject {

    private Long id;
    private Integer bangumiId;
    private String name;
    private String nameCn;
    private String summary;
    private Integer type;           // 默认 2=动画
    private Integer eps;
    private Integer volumes;
    private LocalDate airDate;
    private Integer airWeekday;
    private String image;
    private BigDecimal score;
    @TableField("`rank`")
    private Integer rank;
    private Integer collectionTotal;
    private Boolean nsfw;
    private Integer importStatus;   // 0=待导入 1=已导入
    private LocalDateTime lastImportedAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
