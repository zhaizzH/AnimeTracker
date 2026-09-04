package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("subject_meta_tag")
public class SubjectMetaTag {
    private Long id;                    // 官方标签关联 ID
    private Long subjectId;             // 条目 ID
    private String name;                // 官方标签名
    private Boolean sourceActive;       // 上游是否仍然活跃
    private LocalDateTime createdAt;    // 创建时间
}
