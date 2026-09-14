package top.zhaizz.pojo.vo.subject;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/** 批量权威回查中可返回的条目字段。 */
@Data
public class SubjectBatchItemVO {
    /** 记录或资源的唯一标识。 */
    private Long id;
    /** 来源数据的原始名称。 */
    private String name;
    /** 条目的中文名称。 */
    private String nameCn;
    /** 条目的封面图片地址。 */
    private String image;
    /** 条目评分，取值遵循接口约定。 */
    private BigDecimal score;
    /** 条目评分人数。 */
    private Integer ratingTotal;
    /** 条目收藏人数。 */
    private Integer collectionTotal;
    /** 条目的首播日期。 */
    private LocalDate airDate;
    /** 业务类型或状态编码，取值由所属接口约束。 */
    private Integer type;
    /** 条目是否包含 NSFW 内容。 */
    private Boolean nsfw;
    /** Agent 权威回查需要的有效状态；由 subject.import_status 派生。 */
    private Boolean active;
}
