package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 条目标签关联实体。
 */
@Data
@TableName("subject_tag")
public class SubjectTag {

    /** 标签关联ID。 */
    private Long id;                    // 标签关联ID
    /** 条目ID。 */
    private Long subjectId;             // 条目ID
    /** 标签名。 */
    private String name;                // 标签名
    /** 该标签在此条目上的使用次数（来自 Bangumi API）。 */
    private Integer count;              // 该标签在此条目上的使用次数（来自 Bangumi API）
}
