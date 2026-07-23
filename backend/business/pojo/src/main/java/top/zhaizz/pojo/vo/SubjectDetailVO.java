package top.zhaizz.pojo.vo;

import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 条目详情视图（含标签）
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class SubjectDetailVO extends SubjectListVO {

    private Integer bangumiId;      // Bangumi 外部 ID
    private String summary;
    private Integer volumes;
    private Integer airWeekday;
    private Integer collectionTotal;
    private Boolean nsfw;           // 是否 NSFW
    private List<TagVO> tags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
