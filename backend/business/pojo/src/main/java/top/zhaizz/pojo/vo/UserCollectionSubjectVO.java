package top.zhaizz.pojo.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class UserCollectionSubjectVO {

    private Long id;
    private Long userId;
    private Long subjectId;
    private Integer type;
    private Integer rate;
    private Integer epStatus;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    // subject 表的字段（扁平化 JOIN 结果）
    private String name;
    private String nameCn;
    private String image;
    private BigDecimal score;
    private Integer eps;
    private LocalDate airDate;
    private Integer subjectType;
}
