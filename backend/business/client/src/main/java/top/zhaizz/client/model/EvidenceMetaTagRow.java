package top.zhaizz.client.model;

import lombok.Data;

/** 条目的官方标签行 */
@Data
public class EvidenceMetaTagRow {
    /** 关联条目标识 */
    private Long subjectId;
    /** 来源数据的原始名称 */
    private String name;
}
