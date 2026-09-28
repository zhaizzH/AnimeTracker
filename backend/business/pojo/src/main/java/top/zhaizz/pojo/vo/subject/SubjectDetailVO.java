package top.zhaizz.pojo.vo.subject;

import top.zhaizz.pojo.vo.tag.TagVO;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 条目详情视图（含标签）
 */
public class SubjectDetailVO extends SubjectListVO {

    /** Bangumi API 条目ID */
    private Integer bangumiId;      // Bangumi API 条目ID
    /** 简介/描述 */
    private String summary;         // 简介/描述
    /** 总卷数 */
    private Integer volumes;        // 总卷数
    /** 播出星期（0=周日, 1=周一 ... 6=周六） */
    private Integer airWeekday;     // 播出星期（0=周日, 1=周一 ... 6=周六）
    /** 收藏数 */
    private Integer collectionTotal;// 收藏数
    /** 是否 NSFW: 0=否, 1=是 */
    private Boolean nsfw;           // 是否 NSFW: 0=否, 1=是
    /** 标签列表 */
    private List<TagVO> tags;       // 标签列表
    /** 关联条目列表 */
    private List<SubjectRelationVO> relations = new ArrayList<>();  // 关联条目列表
    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间
    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间

    /** 创建关联条目列表为独立空列表、其余字段默认的空详情 */
    public SubjectDetailVO() {
    }

    /**
     * 获取 Bangumi API 条目ID
     * @return Bangumi 侧条目标识；未提供时为 {@code null}
     */
    public Integer getBangumiId() {
        return this.bangumiId;
    }

    /**
     * 获取简介/描述
     * @return 条目简介；未提供时为 {@code null}
     */
    public String getSummary() {
        return this.summary;
    }

    /**
     * 获取总卷数
     * @return 条目总卷数，动画类型通常为空；未提供时为 {@code null}
     */
    public Integer getVolumes() {
        return this.volumes;
    }

    /**
     * 获取播出星期
     * @return 播出星期；0=周日, 1=周一 ... 6=周六，未提供时为 {@code null}
     */
    public Integer getAirWeekday() {
        return this.airWeekday;
    }

    /**
     * 获取收藏数
     * @return 收藏人数；未提供时为 {@code null}
     */
    public Integer getCollectionTotal() {
        return this.collectionTotal;
    }

    /**
     * 获取是否 NSFW
     * @return 含 NSFW 内容时为 {@code true}；0=否, 1=是，未提供时为 {@code null}
     */
    public Boolean getNsfw() {
        return this.nsfw;
    }

    /**
     * 获取标签列表
     * @return 标签列表；未提供时为 {@code null}
     */
    public List<TagVO> getTags() {
        return this.tags;
    }

    /**
     * 获取关联条目列表
     * @return 关联条目列表；未显式替换时默认为独立空列表
     */
    public List<SubjectRelationVO> getRelations() {
        return this.relations;
    }

    /**
     * 获取创建时间
     * @return 记录创建时间；未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 获取更新时间
     * @return 记录最近更新时间；未提供时为 {@code null}
     */
    public LocalDateTime getUpdatedAt() {
        return this.updatedAt;
    }

    /**
     * 替换 Bangumi API 条目ID
     * @param bangumiId Bangumi 侧条目标识，可为 {@code null}
     */
    public void setBangumiId(final Integer bangumiId) {
        this.bangumiId = bangumiId;
    }

    /**
     * 替换简介/描述
     * @param summary 条目简介，可为 {@code null}
     */
    public void setSummary(final String summary) {
        this.summary = summary;
    }

    /**
     * 替换总卷数
     * @param volumes 条目总卷数，可为 {@code null}
     */
    public void setVolumes(final Integer volumes) {
        this.volumes = volumes;
    }

    /**
     * 替换播出星期
     * @param airWeekday 播出星期，可为 {@code null}；0=周日, 1=周一 ... 6=周六
     */
    public void setAirWeekday(final Integer airWeekday) {
        this.airWeekday = airWeekday;
    }

    /**
     * 替换收藏数
     * @param collectionTotal 收藏人数，可为 {@code null}
     */
    public void setCollectionTotal(final Integer collectionTotal) {
        this.collectionTotal = collectionTotal;
    }

    /**
     * 替换是否 NSFW
     * @param nsfw 含 NSFW 内容时为 {@code true}，可为 {@code null}
     */
    public void setNsfw(final Boolean nsfw) {
        this.nsfw = nsfw;
    }

    /**
     * 替换标签列表
     * @param tags 标签列表，可为 {@code null}；不进行复制
     */
    public void setTags(final List<TagVO> tags) {
        this.tags = tags;
    }

    /**
     * 替换关联条目列表
     * @param relations 关联条目列表，可为 {@code null}；不进行复制
     */
    public void setRelations(final List<SubjectRelationVO> relations) {
        this.relations = relations;
    }

    /**
     * 替换创建时间
     * @param createdAt 记录创建时间，可为 {@code null}
     */
    public void setCreatedAt(final LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 替换更新时间
     * @param updatedAt 记录最近更新时间，可为 {@code null}
     */
    public void setUpdatedAt(final LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    /**
     * 判断与另一对象是否相等，比较父类字段与本类全部字段
     * @param o 待比较的对象
     * @return 类型、父类字段与本类字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectDetailVO)) return false;
        final SubjectDetailVO other = (SubjectDetailVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (!super.equals(o)) return false;
        final Object thisBangumiId = this.getBangumiId();
        final Object otherBangumiId = other.getBangumiId();
        if (thisBangumiId == null ? otherBangumiId != null : !thisBangumiId.equals(otherBangumiId)) return false;
        final Object thisVolumes = this.getVolumes();
        final Object otherVolumes = other.getVolumes();
        if (thisVolumes == null ? otherVolumes != null : !thisVolumes.equals(otherVolumes)) return false;
        final Object thisAirWeekday = this.getAirWeekday();
        final Object otherAirWeekday = other.getAirWeekday();
        if (thisAirWeekday == null ? otherAirWeekday != null : !thisAirWeekday.equals(otherAirWeekday)) return false;
        final Object thisCollectionTotal = this.getCollectionTotal();
        final Object otherCollectionTotal = other.getCollectionTotal();
        if (thisCollectionTotal == null ? otherCollectionTotal != null : !thisCollectionTotal.equals(otherCollectionTotal)) return false;
        final Object thisNsfw = this.getNsfw();
        final Object otherNsfw = other.getNsfw();
        if (thisNsfw == null ? otherNsfw != null : !thisNsfw.equals(otherNsfw)) return false;
        final Object thisSummary = this.getSummary();
        final Object otherSummary = other.getSummary();
        if (thisSummary == null ? otherSummary != null : !thisSummary.equals(otherSummary)) return false;
        final Object thisTags = this.getTags();
        final Object otherTags = other.getTags();
        if (thisTags == null ? otherTags != null : !thisTags.equals(otherTags)) return false;
        final Object thisRelations = this.getRelations();
        final Object otherRelations = other.getRelations();
        if (thisRelations == null ? otherRelations != null : !thisRelations.equals(otherRelations)) return false;
        final Object thisCreatedAt = this.getCreatedAt();
        final Object otherCreatedAt = other.getCreatedAt();
        if (thisCreatedAt == null ? otherCreatedAt != null : !thisCreatedAt.equals(otherCreatedAt)) return false;
        final Object thisUpdatedAt = this.getUpdatedAt();
        final Object otherUpdatedAt = other.getUpdatedAt();
        if (thisUpdatedAt == null ? otherUpdatedAt != null : !thisUpdatedAt.equals(otherUpdatedAt)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 仅当对方同为 {@code SubjectDetailVO} 时为 {@code true}，基类实例不参与
     */
    @Override
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectDetailVO;
    }

    /**
     * 基于父类字段与本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = super.hashCode();
        final Object hashBangumiId = this.getBangumiId();
        result = result * PRIME + (hashBangumiId == null ? 43 : hashBangumiId.hashCode());
        final Object hashVolumes = this.getVolumes();
        result = result * PRIME + (hashVolumes == null ? 43 : hashVolumes.hashCode());
        final Object hashAirWeekday = this.getAirWeekday();
        result = result * PRIME + (hashAirWeekday == null ? 43 : hashAirWeekday.hashCode());
        final Object hashCollectionTotal = this.getCollectionTotal();
        result = result * PRIME + (hashCollectionTotal == null ? 43 : hashCollectionTotal.hashCode());
        final Object hashNsfw = this.getNsfw();
        result = result * PRIME + (hashNsfw == null ? 43 : hashNsfw.hashCode());
        final Object hashSummary = this.getSummary();
        result = result * PRIME + (hashSummary == null ? 43 : hashSummary.hashCode());
        final Object hashTags = this.getTags();
        result = result * PRIME + (hashTags == null ? 43 : hashTags.hashCode());
        final Object hashRelations = this.getRelations();
        result = result * PRIME + (hashRelations == null ? 43 : hashRelations.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        final Object hashUpdatedAt = this.getUpdatedAt();
        result = result * PRIME + (hashUpdatedAt == null ? 43 : hashUpdatedAt.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本，不含父类字段
     */
    @Override
    public String toString() {
        return "SubjectDetailVO(bangumiId=" + this.getBangumiId() + ", summary=" + this.getSummary() + ", volumes=" + this.getVolumes() + ", airWeekday=" + this.getAirWeekday() + ", collectionTotal=" + this.getCollectionTotal() + ", nsfw=" + this.getNsfw() + ", tags=" + this.getTags() + ", relations=" + this.getRelations() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
