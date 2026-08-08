package top.zhaizz.pojo.vo;

import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 条目详情视图（含标签）
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class SubjectDetailVO extends SubjectListVO {

    private Integer bangumiId;      // Bangumi API 条目ID
    private String summary;         // 简介/描述
    private Integer volumes;        // 总卷数
    private Integer airWeekday;     // 播出星期（0=周日, 1=周一 ... 6=周六）
    private Integer collectionTotal;// 收藏数
    private Boolean nsfw;           // 是否 NSFW: 0=否, 1=是
    private List<TagVO> tags;       // 标签列表
    private List<SubjectRelationVO> relations = new ArrayList<>();  // 关联条目列表
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
}
