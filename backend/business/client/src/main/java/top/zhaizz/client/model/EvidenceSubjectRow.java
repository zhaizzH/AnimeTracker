package top.zhaizz.client.model;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/** 条目基础数据行。 */
@Data
public class EvidenceSubjectRow {
    /** 关联条目标识。 */
    private Long subjectId;
    /** 来源数据的原始名称。 */
    private String name;
    /** 条目的中文名称。 */
    private String nameCn;
    /** 业务类型或状态编码。 */
    private Integer type;
    /** 条目是否包含 NSFW 内容。 */
    private Boolean nsfw;
    /** 来源记录是否仍有效。 */
    private Boolean active;
    /** 来源系统中的记录标识。 */
    private Integer sourceId;
    /** 来源记录的原始链接。 */
    private String sourceUrl;
    /** 条目评分。 */
    private BigDecimal score;
    /** 候选结果排序名次。 */
    private Integer rank;
    /** 条目评分人数。 */
    private Integer ratingTotal;
    /** 条目收藏人数。 */
    private Integer collectionTotal;
    /** 条目的首播日期。 */
    private LocalDate airDate;
    /** 条目的播出状态。 */
    private String airStatus;
    /** 条目的简介文本。 */
    private String summary;
    /** 从来源系统抓取数据的时间。 */
    private LocalDateTime sourceFetchedAt;
}
