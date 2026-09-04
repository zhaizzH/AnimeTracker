package top.zhaizz.pojo.dto.evidence;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.List;

/** 批量证据回查请求。 */
@Data
public class EvidenceBatchRequestDTO {

    @NotEmpty(message = "条目 ID 不能为空")
    @Size(max = 50, message = "条目 ID 最多 50 个")
    private List<@NotNull(message = "条目 ID 不能为空") Long> subjectIds;
}
