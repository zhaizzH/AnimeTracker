package top.zhaizz.pojo.vo.subject;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/** MySQL FULLTEXT 召回候选；详细事实仍需通过 Evidence API 回查。 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LexicalSearchCandidateVO {
    private Long subjectId;
    private String name;
    private String nameCn;
    private BigDecimal lexicalScore;
    private Integer rank;
}
