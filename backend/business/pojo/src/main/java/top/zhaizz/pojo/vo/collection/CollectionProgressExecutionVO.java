package top.zhaizz.pojo.vo.collection;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

/**
 * 本周追番进度确认执行结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class CollectionProgressExecutionVO {

    /** 执行状态 */
    private CollectionProgressState state;          // 执行状态
    /** 是否为重复确认返回首次结果 */
    private boolean replayed;                       // 是否为重复确认返回首次结果
    /** 预览变化时的新预览（COMPLETED 时为 null 不输出） */
    private CollectionProgressPreviewVO preview;    // 预览变化时的新预览（COMPLETED 时为 null 不输出）
    /** 执行成功的条目数量 */
    @Builder.Default
    private List<CollectionProgressItemVO> succeeded = new ArrayList<>();
    /** 执行时跳过的条目数量 */
    @Builder.Default
    private List<CollectionProgressFailureVO> skipped = new ArrayList<>();
    /** 执行失败的条目数量 */
    @Builder.Default
    private List<CollectionProgressFailureVO> failed = new ArrayList<>();
}
