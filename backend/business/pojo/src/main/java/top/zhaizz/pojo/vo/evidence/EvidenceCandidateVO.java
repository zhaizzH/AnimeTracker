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
 * 面向 Agent 的条目证据视图。
 * 包含标题、别名、标签、主创、角色、关联条目等完整证据链。
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EvidenceCandidateVO {

    private Long subjectId;
    private String name;
    private String nameCn;
    private Integer type;
    private Boolean nsfw;
    /** 当前记录是否仍是可供 Agent 使用的活跃来源事实。 */
    private Boolean active;
    /** 上游 Bangumi ID。 */
    private Integer sourceId;
    /** 上游 Bangumi 详情 URL。 */
    private String sourceUrl;
    private BigDecimal score;
    private Integer rank;
    private Integer ratingTotal;
    private Integer collectionTotal;
    private LocalDate airDate;
    private String summary;

    private List<String> aliases;
    private List<String> metaTags;
    private List<CreditItem> credits;
    private List<CharacterItem> characters;
    private List<RelationItem> relations;

    private LocalDateTime sourceTime;
    /** 新字段名；sourceTime 保留用于旧 Agent/客户端兼容。 */
    private LocalDateTime sourceFetchedAt;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CreditItem {
        private String personName;
        private String role;
        private String relation;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CharacterItem {
        private String characterName;
        private String relation;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RelationItem {
        private Long relatedSubjectId;
        private String relatedSubjectName;
        private String relatedSubjectNameCn;
        private String relation;
    }
}
