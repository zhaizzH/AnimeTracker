package top.zhaizz.pojo.dto.evidence;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 按实体批量扩展至安全动画条目的请求。
 * <p>
 * ids 始终是本地数据库主键；人物声优（ACTOR）同样使用 person.id，
 * 仅关系路径不同。
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class EvidenceEntityBatchRequestDTO {

    @NotNull(message = "实体类型不能为空")
    private EvidenceEntityType entityType;

    @NotEmpty(message = "实体 ID 不能为空")
    @Size(max = 50, message = "实体 ID 最多 50 个")
    private List<@NotNull(message = "实体 ID 不能为空") @Positive(message = "实体 ID 必须为正数") Long> ids;
}
