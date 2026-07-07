package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 条目-标签关联实体
 */
@Data
@TableName("subject_tag")
public class SubjectTag {

    private Long id;
    private Long subjectId;
    private String name;
    private Integer count;
}
