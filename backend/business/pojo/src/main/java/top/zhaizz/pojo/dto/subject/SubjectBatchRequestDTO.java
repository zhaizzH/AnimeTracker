package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.List;

/** 批量权威回查请求。 */
@Data
public class SubjectBatchRequestDTO {

    /**
     * 待回查条目 ID，必填且最多 100 个，元素不得为空。
     */
    @NotEmpty(message = "条目 ID 不能为空")
    @Size(max = 100, message = "条目 ID 最多 100 个")
    private List<@NotNull(message = "条目 ID 不能为空") Long> subjectIds;

    /** 是否排除已收藏条目。 */
    private boolean excludeCollected;
}
