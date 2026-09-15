package top.zhaizz.client.model;

import lombok.Data;

/** 条目角色行（含角色名称） */
@Data
public class EvidenceCharacterRow {
    /** 关联条目标识 */
    private Long subjectId;
    /** 角色名称 */
    private String characterName;
    /** 实体之间的关系类型 */
    private String relation;
}
