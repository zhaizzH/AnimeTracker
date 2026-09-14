package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 角色别名实体。
 */
@Data
@TableName("character_alias")
public class CharacterAlias {

    /** 别名ID。 */
    private Long id;                    // 别名ID
    /** 角色ID。 */
    private Long characterId;           // 角色ID
    /** 别名。 */
    private String name;                // 别名
    /** 语言。 */
    private String language;            // 语言
    /** 来源。 */
    private String source;              // 来源
    /** 上游是否仍然活跃。 */
    private Boolean sourceActive;       // 上游是否仍然活跃
    /** 创建时间。 */
    private LocalDateTime createdAt;    // 创建时间
    /** 更新时间。 */
    private LocalDateTime updatedAt;    // 更新时间
}
