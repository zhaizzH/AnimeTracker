package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.List;

/** 批量权威回查请求。 */
@Data
public class SubjectBatchRequestDTO {

    @NotEmpty(message = "条目 ID 不能为空")
    @Size(max = 100, message = "条目 ID 最多 100 个")
    private List<@NotNull(message = "条目 ID 不能为空") Long> subjectIds;

    private boolean excludeCollected;
}
