package top.zhaizz.pojo.vo.subject;

import lombok.Data;
import lombok.EqualsAndHashCode;
import top.zhaizz.pojo.vo.tag.TagVO;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 条目详情视图（含标签）。
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class SubjectDetailVO extends SubjectListVO {

    /** Bangumi API 条目ID。 */
    private Integer bangumiId;      // Bangumi API 条目ID
    /** 简介/描述。 */
    private String summary;         // 简介/描述
    /** 总卷数。 */
    private Integer volumes;        // 总卷数
    /** 播出星期（0=周日, 1=周一 ... 6=周六）。 */
    private Integer airWeekday;     // 播出星期（0=周日, 1=周一 ... 6=周六）
    /** 收藏数。 */
    private Integer collectionTotal;// 收藏数
    /** 是否 NSFW: 0=否, 1=是。 */
    private Boolean nsfw;           // 是否 NSFW: 0=否, 1=是
    /** 标签列表。 */
    private List<TagVO> tags;       // 标签列表
    /** 关联条目列表。 */
    private List<SubjectRelationVO> relations = new ArrayList<>();  // 关联条目列表
    /** 创建时间。 */
    private LocalDateTime createdAt;    // 创建时间
    /** 更新时间。 */
    private LocalDateTime updatedAt;    // 更新时间
}
