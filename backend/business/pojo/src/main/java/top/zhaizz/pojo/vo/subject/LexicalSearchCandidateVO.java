package top.zhaizz.pojo.vo.subject;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/** MySQL FULLTEXT 召回候选；详细事实仍需通过 Evidence API 回查 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LexicalSearchCandidateVO {
    /** 关联条目标识 */
    private Long subjectId;
    /** 来源数据的原始名称 */
    private String name;
    /** 条目的中文名称 */
    private String nameCn;
    /** 词法检索相关性得分 */
    private BigDecimal lexicalScore;
    /** 候选结果排序名次 */
    private Integer rank;
}
