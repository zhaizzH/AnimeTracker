package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 条目-角色关联实体
 */
@Data
@TableName("subject_character")
public class SubjectCharacter {

    private Long id;                    // 关联ID
    private Long subjectId;             // 条目ID
    private Long characterId;           // 角色ID
    private String relation;            // 角色在作品中的定位: MAIN=主角, SUPPORTING=配角, GUEST=客串
    private Integer sortOrder;          // 来源排序
    private Boolean sourceActive;       // 上游是否仍然活跃
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
}
