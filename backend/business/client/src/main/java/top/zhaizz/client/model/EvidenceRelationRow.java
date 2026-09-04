package top.zhaizz.client.model;

import lombok.Data;

/** 条目关联行（含关联条目标题）。 */
@Data
public class EvidenceRelationRow {
    private Long subjectId;
    private Long relatedSubjectId;
    private String relatedSubjectName;
    private String relatedSubjectNameCn;
    private String relation;
}
