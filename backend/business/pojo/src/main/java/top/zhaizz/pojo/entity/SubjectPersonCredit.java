package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 条目-人物主创关联实体
 */
@Data
@TableName("subject_person_credit")
public class SubjectPersonCredit {

    /** 关联ID */
    private Long id;                    // 关联ID
    /** 条目ID */
    private Long subjectId;             // 条目ID
    /** 人物ID */
    private Long personId;              // 人物ID
    /** 职责（如导演、脚本） */
    private String role;                // 职责（如导演、脚本）
    /** 关系类型: MAIN=主要, SUB=次要 */
    private String relation;            // 关系类型: MAIN=主要, SUB=次要
    /** 来源排序 */
    private Integer sortOrder;          // 来源排序
    /** 上游是否仍然活跃 */
    private Boolean sourceActive;       // 上游是否仍然活跃
    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间
    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间
}
