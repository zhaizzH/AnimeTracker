package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 人物别名实体
 */
@Data
@TableName("person_alias")
public class PersonAlias {

    private Long id;                    // 别名ID
    private Long personId;              // 人物ID
    private String name;                // 别名
    private String language;            // 语言
    private String source;              // 来源
    private Boolean sourceActive;       // 上游是否仍然活跃
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
}
