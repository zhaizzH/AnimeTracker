package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 角色-声优关联实体（限定于特定作品）
 */
@Data
@TableName("character_actor")
public class CharacterActor {

    private Long id;                    // 关联ID
    private Long subjectId;             // 条目ID（声优关系限定于特定作品版本）
    private Long characterId;           // 角色ID
    private Long personId;              // 声优人物ID
    private String actorRelation;       // 演员关系: VA=声优, ACTOR=真人演员
    private Integer sortOrder;          // 来源排序
    private Boolean sourceActive;       // 上游是否仍然活跃
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
}
