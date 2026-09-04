package top.zhaizz.client.model;

import lombok.Data;

/** 条目主创人员行（含人物名称）。 */
@Data
public class EvidenceCreditRow {
    private Long subjectId;
    private String personName;
    private String role;
    private String relation;
}
