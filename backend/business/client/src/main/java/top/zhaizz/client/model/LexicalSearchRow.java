package top.zhaizz.client.model;

import lombok.Data;

import java.math.BigDecimal;

/** search_document 的受控词法召回行。 */
@Data
public class LexicalSearchRow {
    private Long subjectId;
    private String name;
    private String nameCn;
    private BigDecimal lexicalScore;
}
