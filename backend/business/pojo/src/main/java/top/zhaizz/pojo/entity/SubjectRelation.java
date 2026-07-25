package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 条目关联实体
 */
@Data
@TableName("subject_relation")
public class SubjectRelation {

    private Long id;
    private Long subjectId;
    private Long relatedSubjectId;
    private String relation;  // prequel, sequel, side_story 等
}
