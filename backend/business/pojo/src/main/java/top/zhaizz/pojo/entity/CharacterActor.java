package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 角色-声优关联实体（限定于特定作品）。
 */
@Data
@TableName("character_actor")
public class CharacterActor {

    /** 关联ID。 */
    private Long id;                    // 关联ID
    /** 条目ID（声优关系限定于特定作品版本）。 */
    private Long subjectId;             // 条目ID（声优关系限定于特定作品版本）
    /** 角色ID。 */
    private Long characterId;           // 角色ID
    /** 声优人物ID。 */
    private Long personId;              // 声优人物ID
    /** 演员关系: VA=声优, ACTOR=真人演员。 */
    private String actorRelation;       // 演员关系: VA=声优, ACTOR=真人演员
    /** 来源排序。 */
    private Integer sortOrder;          // 来源排序
    /** 上游是否仍然活跃。 */
    private Boolean sourceActive;       // 上游是否仍然活跃
    /** 创建时间。 */
    private LocalDateTime createdAt;    // 创建时间
    /** 更新时间。 */
    private LocalDateTime updatedAt;    // 更新时间
}
