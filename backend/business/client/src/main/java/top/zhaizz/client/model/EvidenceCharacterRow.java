package top.zhaizz.client.model;

import lombok.Data;

/** 条目角色行（含角色名称）。 */
@Data
public class EvidenceCharacterRow {
    private Long subjectId;
    private String characterName;
    private String relation;
}
