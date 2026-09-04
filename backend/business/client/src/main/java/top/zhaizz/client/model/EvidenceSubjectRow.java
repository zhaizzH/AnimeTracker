package top.zhaizz.client.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/** 条目基础数据行。 */
@Data
public class EvidenceSubjectRow {
    private Long subjectId;
    private String name;
    private String nameCn;
    private Integer type;
    private Boolean nsfw;
    private BigDecimal score;
    private Integer rank;
    private Integer ratingTotal;
    private Integer collectionTotal;
    private LocalDate airDate;
    private String summary;
    private LocalDateTime sourceFetchedAt;
}
