package top.zhaizz.client.model;

import lombok.Data;

/** 条目主创人员行（含人物名称） */
@Data
public class EvidenceCreditRow {
    /** 关联条目标识 */
    private Long subjectId;
    /** 人物名称 */
    private String personName;
    /** 人员或角色在关系中的职务 */
    private String role;
    /** 实体之间的关系类型 */
    private String relation;
}
