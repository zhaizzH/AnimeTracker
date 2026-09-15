package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/** SubjectMetaTag 数据对象 */
@Data
@TableName("subject_meta_tag")
public class SubjectMetaTag {
    /** 官方标签关联 ID */
    private Long id;                    // 官方标签关联 ID
    /** 条目 ID */
    private Long subjectId;             // 条目 ID
    /** 官方标签名 */
    private String name;                // 官方标签名
    /** 上游是否仍然活跃 */
    private Boolean sourceActive;       // 上游是否仍然活跃
    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间
}
