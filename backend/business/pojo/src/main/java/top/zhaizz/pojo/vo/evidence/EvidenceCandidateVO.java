package top.zhaizz.pojo.vo.evidence;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 面向 Agent 的条目证据视图
 * 包含标题、别名、标签、主创、角色、关联条目等完整证据链
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EvidenceCandidateVO {

    /** 关联条目标识 */
    private Long subjectId;
    /** 来源数据的原始名称 */
    private String name;
    /** 条目的中文名称 */
    private String nameCn;
    /** 业务类型或状态编码，取值由所属接口约束 */
    private Integer type;
    /** 条目是否包含 NSFW 内容 */
    private Boolean nsfw;
    /** 当前记录是否仍是可供 Agent 使用的活跃来源事实 */
    private Boolean active;
    /** 上游 Bangumi ID */
    private Integer sourceId;
    /** 上游 Bangumi 详情 URL */
    private String sourceUrl;
    /** 条目评分，取值遵循接口约定 */
    private BigDecimal score;
    /** 候选结果排序名次 */
    private Integer rank;
    /** 条目评分人数 */
    private Integer ratingTotal;
    /** 条目收藏人数 */
    private Integer collectionTotal;
    /** 条目的首播日期 */
    private LocalDate airDate;
    /** 基于条目日期与剧集状态推导的播出状态 */
    private String airStatus;
    /** 条目的简介文本 */
    private String summary;

    /** 条目的别名列表 */
    private List<String> aliases;
    /** 条目关联的元标签列表 */
    private List<String> metaTags;
    /** 条目演职人员列表 */
    private List<CreditItem> credits;
    /** 条目关联的角色列表 */
    private List<CharacterItem> characters;
    /** 条目关联关系列表 */
    private List<RelationItem> relations;

    /** 来源数据对应的时间点 */
    private LocalDateTime sourceTime;
    /** 新字段名；sourceTime 保留用于旧 Agent/客户端兼容 */
    private LocalDateTime sourceFetchedAt;

    /** CreditItem 数据对象 */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CreditItem {
        /** 人物名称 */
        private String personName;
        /** 人员或角色在关系中的职务 */
        private String role;
        /** 实体之间的关系类型 */
        private String relation;
    }

    /** CharacterItem 数据对象 */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CharacterItem {
        /** 角色名称 */
        private String characterName;
        /** 实体之间的关系类型 */
        private String relation;
    }

    /** RelationItem 数据对象 */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RelationItem {
        /** 关联条目标识 */
        private Long relatedSubjectId;
        /** 关联条目的原始名称 */
        private String relatedSubjectName;
        /** 关联条目的中文名称 */
        private String relatedSubjectNameCn;
        /** 实体之间的关系类型 */
        private String relation;
    }
}
