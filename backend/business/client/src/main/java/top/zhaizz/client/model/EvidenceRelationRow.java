package top.zhaizz.client.model;

import lombok.Data;

/** 条目关联行（含关联条目标题） */
@Data
public class EvidenceRelationRow {
    /** 关联条目标识 */
    private Long subjectId;
    /** 关联条目标识 */
    private Long relatedSubjectId;
    /** 关联条目的原始名称 */
    private String relatedSubjectName;
    /** 关联条目的中文名称 */
    private String relatedSubjectNameCn;
    /** 实体之间的关系类型 */
    private String relation;
}
