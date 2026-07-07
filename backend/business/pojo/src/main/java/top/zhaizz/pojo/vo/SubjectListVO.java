package top.zhaizz.pojo.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 条目列表视图（摘要信息）
 */
@Data
public class SubjectListVO {

    private Long id;
    private String name;
    private String nameCn;
    private String image;
    private BigDecimal score;
    private Integer rank;
    private Integer eps;
    private LocalDate airDate;
    private Integer type;
}
