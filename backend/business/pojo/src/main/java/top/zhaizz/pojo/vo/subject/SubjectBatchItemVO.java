package top.zhaizz.pojo.vo.subject;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/** 批量权威回查中可返回的条目字段。 */
@Data
public class SubjectBatchItemVO {
    private Long id;
    private String name;
    private String nameCn;
    private String image;
    private BigDecimal score;
    private Integer ratingTotal;
    private Integer collectionTotal;
    private LocalDate airDate;
    private Integer type;
    private Boolean nsfw;
}
