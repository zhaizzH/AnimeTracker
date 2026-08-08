package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 条目关联实体
 */
@Data
@TableName("subject_relation")
public class SubjectRelation {

    private Long id;                    // 关联ID
    private Long subjectId;             // 当前条目ID
    private Long relatedSubjectId;      // 关联条目ID
    private String relation;            // 关联类型: prequel, sequel, side_story 等
}
