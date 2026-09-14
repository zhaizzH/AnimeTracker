package top.zhaizz.client.model;

import lombok.Data;

import java.math.BigDecimal;

/** search_document 的受控词法召回行。 */
@Data
public class LexicalSearchRow {
    /** 关联条目标识。 */
    private Long subjectId;
    /** 来源数据的原始名称。 */
    private String name;
    /** 条目的中文名称。 */
    private String nameCn;
    /** 词法检索相关性得分。 */
    private BigDecimal lexicalScore;
}
