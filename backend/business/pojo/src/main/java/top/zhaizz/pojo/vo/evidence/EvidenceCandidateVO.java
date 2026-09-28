package top.zhaizz.pojo.vo.evidence;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 面向 Agent 的条目证据视图
 * 包含标题、别名、标签、主创、角色、关联条目等完整证据链
 */
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

    /** 创建字段均为默认值的空证据视图 */
    public EvidenceCandidateVO() {
    }

    /**
     * 创建携带全部字段的证据视图
     * @param subjectId 关联条目标识，可为 {@code null}
     * @param name 来源数据的原始名称，可为 {@code null}
     * @param nameCn 条目的中文名称，可为 {@code null}
     * @param type 业务类型或状态编码，可为 {@code null}
     * @param nsfw 条目是否包含 NSFW 内容，可为 {@code null}
     * @param active 当前记录是否仍是活跃来源事实，可为 {@code null}
     * @param sourceId 上游 Bangumi ID，可为 {@code null}
     * @param sourceUrl 上游 Bangumi 详情 URL，可为 {@code null}
     * @param score 条目评分，可为 {@code null}
     * @param rank 候选结果排序名次，可为 {@code null}
     * @param ratingTotal 条目评分人数，可为 {@code null}
     * @param collectionTotal 条目收藏人数，可为 {@code null}
     * @param airDate 条目的首播日期，可为 {@code null}
     * @param airStatus 推导得到的播出状态，可为 {@code null}
     * @param summary 条目的简介文本，可为 {@code null}
     * @param aliases 条目的别名列表，可为 {@code null}；不进行复制
     * @param metaTags 条目关联的元标签列表，可为 {@code null}；不进行复制
     * @param credits 条目演职人员列表，可为 {@code null}；不进行复制
     * @param characters 条目关联的角色列表，可为 {@code null}；不进行复制
     * @param relations 条目关联关系列表，可为 {@code null}；不进行复制
     * @param sourceTime 来源数据对应的时间点，可为 {@code null}
     * @param sourceFetchedAt 新字段名的来源抓取时间点，可为 {@code null}
     */
    public EvidenceCandidateVO(final Long subjectId, final String name, final String nameCn, final Integer type, final Boolean nsfw, final Boolean active, final Integer sourceId, final String sourceUrl, final BigDecimal score, final Integer rank, final Integer ratingTotal, final Integer collectionTotal, final LocalDate airDate, final String airStatus, final String summary, final List<String> aliases, final List<String> metaTags, final List<CreditItem> credits, final List<CharacterItem> characters, final List<RelationItem> relations, final LocalDateTime sourceTime, final LocalDateTime sourceFetchedAt) {
        this.subjectId = subjectId;
        this.name = name;
        this.nameCn = nameCn;
        this.type = type;
        this.nsfw = nsfw;
        this.active = active;
        this.sourceId = sourceId;
        this.sourceUrl = sourceUrl;
        this.score = score;
        this.rank = rank;
        this.ratingTotal = ratingTotal;
        this.collectionTotal = collectionTotal;
        this.airDate = airDate;
        this.airStatus = airStatus;
        this.summary = summary;
        this.aliases = aliases;
        this.metaTags = metaTags;
        this.credits = credits;
        this.characters = characters;
        this.relations = relations;
        this.sourceTime = sourceTime;
        this.sourceFetchedAt = sourceFetchedAt;
    }

    /**
     * 创建构建器，用于链式组装证据视图
     * @return 空的证据视图构建器
     */
    public static EvidenceCandidateVOBuilder builder() {
        return new EvidenceCandidateVOBuilder();
    }

    /**
     * 获取关联条目标识
     * @return 关联的条目ID；未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取来源数据的原始名称
     * @return 来源中的条目原始名称；未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取条目的中文名称
     * @return 条目中文名；未提供时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取业务类型或状态编码
     * @return 业务类型或状态编码，取值由所属接口约束；未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取是否包含 NSFW 内容
     * @return 条目包含 NSFW 内容时为 {@code true}；未提供时为 {@code null}
     */
    public Boolean getNsfw() {
        return this.nsfw;
    }

    /**
     * 获取来源事实是否仍活跃
     * @return 记录仍可供 Agent 使用时为 {@code true}；未提供时为 {@code null}
     */
    public Boolean getActive() {
        return this.active;
    }

    /**
     * 获取上游 Bangumi ID
     * @return 上游 Bangumi 中的条目ID；未提供时为 {@code null}
     */
    public Integer getSourceId() {
        return this.sourceId;
    }

    /**
     * 获取上游 Bangumi 详情 URL
     * @return 上游 Bangumi 条目详情地址；未提供时为 {@code null}
     */
    public String getSourceUrl() {
        return this.sourceUrl;
    }

    /**
     * 获取条目评分
     * @return 条目评分，取值遵循接口约定；未提供时为 {@code null}
     */
    public BigDecimal getScore() {
        return this.score;
    }

    /**
     * 获取候选结果排序名次
     * @return 候选结果中的排序名次；未提供时为 {@code null}
     */
    public Integer getRank() {
        return this.rank;
    }

    /**
     * 获取条目评分人数
     * @return 为该条目打分的总人数；未提供时为 {@code null}
     */
    public Integer getRatingTotal() {
        return this.ratingTotal;
    }

    /**
     * 获取条目收藏人数
     * @return 收藏该条目的总人数；未提供时为 {@code null}
     */
    public Integer getCollectionTotal() {
        return this.collectionTotal;
    }

    /**
     * 获取条目的首播日期
     * @return 条目首播日期；未提供时为 {@code null}
     */
    public LocalDate getAirDate() {
        return this.airDate;
    }

    /**
     * 获取播出状态
     * @return 由条目日期与剧集状态推导的播出状态；未提供时为 {@code null}
     */
    public String getAirStatus() {
        return this.airStatus;
    }

    /**
     * 获取条目的简介文本
     * @return 条目简介；未提供时为 {@code null}
     */
    public String getSummary() {
        return this.summary;
    }

    /**
     * 获取条目的别名列表
     * @return 别名列表；未提供时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public List<String> getAliases() {
        return this.aliases;
    }

    /**
     * 获取条目关联的元标签列表
     * @return 元标签列表；未提供时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public List<String> getMetaTags() {
        return this.metaTags;
    }

    /**
     * 获取条目演职人员列表
     * @return 演职人员列表；未提供时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public List<CreditItem> getCredits() {
        return this.credits;
    }

    /**
     * 获取条目关联的角色列表
     * @return 角色列表；未提供时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public List<CharacterItem> getCharacters() {
        return this.characters;
    }

    /**
     * 获取条目关联关系列表
     * @return 关联关系列表；未提供时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public List<RelationItem> getRelations() {
        return this.relations;
    }

    /**
     * 获取来源数据对应的时间点
     * @return 来源数据时间点；未提供时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public LocalDateTime getSourceTime() {
        return this.sourceTime;
    }

    /**
     * 获取来源抓取时间点
     * @return 新字段名的来源抓取时间点；未提供时为 {@code null}
     */
    public LocalDateTime getSourceFetchedAt() {
        return this.sourceFetchedAt;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 关联的条目ID，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换来源数据的原始名称
     * @param name 来源中的条目原始名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换条目的中文名称
     * @param nameCn 条目中文名，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换业务类型或状态编码
     * @param type 业务类型或状态编码，取值由所属接口约束，可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换是否包含 NSFW 内容
     * @param nsfw 条目包含 NSFW 内容时为 {@code true}，可为 {@code null}
     */
    public void setNsfw(final Boolean nsfw) {
        this.nsfw = nsfw;
    }

    /**
     * 替换来源事实是否仍活跃
     * @param active 记录仍可供 Agent 使用时为 {@code true}，可为 {@code null}
     */
    public void setActive(final Boolean active) {
        this.active = active;
    }

    /**
     * 替换上游 Bangumi ID
     * @param sourceId 上游 Bangumi 中的条目ID，可为 {@code null}
     */
    public void setSourceId(final Integer sourceId) {
        this.sourceId = sourceId;
    }

    /**
     * 替换上游 Bangumi 详情 URL
     * @param sourceUrl 上游 Bangumi 条目详情地址，可为 {@code null}
     */
    public void setSourceUrl(final String sourceUrl) {
        this.sourceUrl = sourceUrl;
    }

    /**
     * 替换条目评分
     * @param score 条目评分，取值遵循接口约定，可为 {@code null}
     */
    public void setScore(final BigDecimal score) {
        this.score = score;
    }

    /**
     * 替换候选结果排序名次
     * @param rank 候选结果中的排序名次，可为 {@code null}
     */
    public void setRank(final Integer rank) {
        this.rank = rank;
    }

    /**
     * 替换条目评分人数
     * @param ratingTotal 为该条目打分的总人数，可为 {@code null}
     */
    public void setRatingTotal(final Integer ratingTotal) {
        this.ratingTotal = ratingTotal;
    }

    /**
     * 替换条目收藏人数
     * @param collectionTotal 收藏该条目的总人数，可为 {@code null}
     */
    public void setCollectionTotal(final Integer collectionTotal) {
        this.collectionTotal = collectionTotal;
    }

    /**
     * 替换条目的首播日期
     * @param airDate 条目首播日期，可为 {@code null}
     */
    public void setAirDate(final LocalDate airDate) {
        this.airDate = airDate;
    }

    /**
     * 替换播出状态
     * @param airStatus 由条目日期与剧集状态推导的播出状态，可为 {@code null}
     */
    public void setAirStatus(final String airStatus) {
        this.airStatus = airStatus;
    }

    /**
     * 替换条目的简介文本
     * @param summary 条目简介，可为 {@code null}
     */
    public void setSummary(final String summary) {
        this.summary = summary;
    }

    /**
     * 替换条目的别名列表
     * @param aliases 别名列表，可为 {@code null}；不进行复制
     */
    public void setAliases(final List<String> aliases) {
        this.aliases = aliases;
    }

    /**
     * 替换条目关联的元标签列表
     * @param metaTags 元标签列表，可为 {@code null}；不进行复制
     */
    public void setMetaTags(final List<String> metaTags) {
        this.metaTags = metaTags;
    }

    /**
     * 替换条目演职人员列表
     * @param credits 演职人员列表，可为 {@code null}；不进行复制
     */
    public void setCredits(final List<CreditItem> credits) {
        this.credits = credits;
    }

    /**
     * 替换条目关联的角色列表
     * @param characters 角色列表，可为 {@code null}；不进行复制
     */
    public void setCharacters(final List<CharacterItem> characters) {
        this.characters = characters;
    }

    /**
     * 替换条目关联关系列表
     * @param relations 关联关系列表，可为 {@code null}；不进行复制
     */
    public void setRelations(final List<RelationItem> relations) {
        this.relations = relations;
    }

    /**
     * 替换来源数据对应的时间点
     * @param sourceTime 来源数据时间点，可为 {@code null}
     */
    public void setSourceTime(final LocalDateTime sourceTime) {
        this.sourceTime = sourceTime;
    }

    /**
     * 替换来源抓取时间点
     * @param sourceFetchedAt 新字段名的来源抓取时间点，可为 {@code null}
     */
    public void setSourceFetchedAt(final LocalDateTime sourceFetchedAt) {
        this.sourceFetchedAt = sourceFetchedAt;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof EvidenceCandidateVO)) return false;
        final EvidenceCandidateVO other = (EvidenceCandidateVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisNsfw = this.getNsfw();
        final Object otherNsfw = other.getNsfw();
        if (thisNsfw == null ? otherNsfw != null : !thisNsfw.equals(otherNsfw)) return false;
        final Object thisActive = this.getActive();
        final Object otherActive = other.getActive();
        if (thisActive == null ? otherActive != null : !thisActive.equals(otherActive)) return false;
        final Object thisSourceId = this.getSourceId();
        final Object otherSourceId = other.getSourceId();
        if (thisSourceId == null ? otherSourceId != null : !thisSourceId.equals(otherSourceId)) return false;
        final Object thisRank = this.getRank();
        final Object otherRank = other.getRank();
        if (thisRank == null ? otherRank != null : !thisRank.equals(otherRank)) return false;
        final Object thisRatingTotal = this.getRatingTotal();
        final Object otherRatingTotal = other.getRatingTotal();
        if (thisRatingTotal == null ? otherRatingTotal != null : !thisRatingTotal.equals(otherRatingTotal)) return false;
        final Object thisCollectionTotal = this.getCollectionTotal();
        final Object otherCollectionTotal = other.getCollectionTotal();
        if (thisCollectionTotal == null ? otherCollectionTotal != null : !thisCollectionTotal.equals(otherCollectionTotal)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisNameCn = this.getNameCn();
        final Object otherNameCn = other.getNameCn();
        if (thisNameCn == null ? otherNameCn != null : !thisNameCn.equals(otherNameCn)) return false;
        final Object thisSourceUrl = this.getSourceUrl();
        final Object otherSourceUrl = other.getSourceUrl();
        if (thisSourceUrl == null ? otherSourceUrl != null : !thisSourceUrl.equals(otherSourceUrl)) return false;
        final Object thisScore = this.getScore();
        final Object otherScore = other.getScore();
        if (thisScore == null ? otherScore != null : !thisScore.equals(otherScore)) return false;
        final Object thisAirDate = this.getAirDate();
        final Object otherAirDate = other.getAirDate();
        if (thisAirDate == null ? otherAirDate != null : !thisAirDate.equals(otherAirDate)) return false;
        final Object thisAirStatus = this.getAirStatus();
        final Object otherAirStatus = other.getAirStatus();
        if (thisAirStatus == null ? otherAirStatus != null : !thisAirStatus.equals(otherAirStatus)) return false;
        final Object thisSummary = this.getSummary();
        final Object otherSummary = other.getSummary();
        if (thisSummary == null ? otherSummary != null : !thisSummary.equals(otherSummary)) return false;
        final Object thisAliases = this.getAliases();
        final Object otherAliases = other.getAliases();
        if (thisAliases == null ? otherAliases != null : !thisAliases.equals(otherAliases)) return false;
        final Object thisMetaTags = this.getMetaTags();
        final Object otherMetaTags = other.getMetaTags();
        if (thisMetaTags == null ? otherMetaTags != null : !thisMetaTags.equals(otherMetaTags)) return false;
        final Object thisCredits = this.getCredits();
        final Object otherCredits = other.getCredits();
        if (thisCredits == null ? otherCredits != null : !thisCredits.equals(otherCredits)) return false;
        final Object thisCharacters = this.getCharacters();
        final Object otherCharacters = other.getCharacters();
        if (thisCharacters == null ? otherCharacters != null : !thisCharacters.equals(otherCharacters)) return false;
        final Object thisRelations = this.getRelations();
        final Object otherRelations = other.getRelations();
        if (thisRelations == null ? otherRelations != null : !thisRelations.equals(otherRelations)) return false;
        final Object thisSourceTime = this.getSourceTime();
        final Object otherSourceTime = other.getSourceTime();
        if (thisSourceTime == null ? otherSourceTime != null : !thisSourceTime.equals(otherSourceTime)) return false;
        final Object thisSourceFetchedAt = this.getSourceFetchedAt();
        final Object otherSourceFetchedAt = other.getSourceFetchedAt();
        if (thisSourceFetchedAt == null ? otherSourceFetchedAt != null : !thisSourceFetchedAt.equals(otherSourceFetchedAt)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof EvidenceCandidateVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashNsfw = this.getNsfw();
        result = result * PRIME + (hashNsfw == null ? 43 : hashNsfw.hashCode());
        final Object hashActive = this.getActive();
        result = result * PRIME + (hashActive == null ? 43 : hashActive.hashCode());
        final Object hashSourceId = this.getSourceId();
        result = result * PRIME + (hashSourceId == null ? 43 : hashSourceId.hashCode());
        final Object hashRank = this.getRank();
        result = result * PRIME + (hashRank == null ? 43 : hashRank.hashCode());
        final Object hashRatingTotal = this.getRatingTotal();
        result = result * PRIME + (hashRatingTotal == null ? 43 : hashRatingTotal.hashCode());
        final Object hashCollectionTotal = this.getCollectionTotal();
        result = result * PRIME + (hashCollectionTotal == null ? 43 : hashCollectionTotal.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashNameCn = this.getNameCn();
        result = result * PRIME + (hashNameCn == null ? 43 : hashNameCn.hashCode());
        final Object hashSourceUrl = this.getSourceUrl();
        result = result * PRIME + (hashSourceUrl == null ? 43 : hashSourceUrl.hashCode());
        final Object hashScore = this.getScore();
        result = result * PRIME + (hashScore == null ? 43 : hashScore.hashCode());
        final Object hashAirDate = this.getAirDate();
        result = result * PRIME + (hashAirDate == null ? 43 : hashAirDate.hashCode());
        final Object hashAirStatus = this.getAirStatus();
        result = result * PRIME + (hashAirStatus == null ? 43 : hashAirStatus.hashCode());
        final Object hashSummary = this.getSummary();
        result = result * PRIME + (hashSummary == null ? 43 : hashSummary.hashCode());
        final Object hashAliases = this.getAliases();
        result = result * PRIME + (hashAliases == null ? 43 : hashAliases.hashCode());
        final Object hashMetaTags = this.getMetaTags();
        result = result * PRIME + (hashMetaTags == null ? 43 : hashMetaTags.hashCode());
        final Object hashCredits = this.getCredits();
        result = result * PRIME + (hashCredits == null ? 43 : hashCredits.hashCode());
        final Object hashCharacters = this.getCharacters();
        result = result * PRIME + (hashCharacters == null ? 43 : hashCharacters.hashCode());
        final Object hashRelations = this.getRelations();
        result = result * PRIME + (hashRelations == null ? 43 : hashRelations.hashCode());
        final Object hashSourceTime = this.getSourceTime();
        result = result * PRIME + (hashSourceTime == null ? 43 : hashSourceTime.hashCode());
        final Object hashSourceFetchedAt = this.getSourceFetchedAt();
        result = result * PRIME + (hashSourceFetchedAt == null ? 43 : hashSourceFetchedAt.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "EvidenceCandidateVO(subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", type=" + this.getType() + ", nsfw=" + this.getNsfw() + ", active=" + this.getActive() + ", sourceId=" + this.getSourceId() + ", sourceUrl=" + this.getSourceUrl() + ", score=" + this.getScore() + ", rank=" + this.getRank() + ", ratingTotal=" + this.getRatingTotal() + ", collectionTotal=" + this.getCollectionTotal() + ", airDate=" + this.getAirDate() + ", airStatus=" + this.getAirStatus() + ", summary=" + this.getSummary() + ", aliases=" + this.getAliases() + ", metaTags=" + this.getMetaTags() + ", credits=" + this.getCredits() + ", characters=" + this.getCharacters() + ", relations=" + this.getRelations() + ", sourceTime=" + this.getSourceTime() + ", sourceFetchedAt=" + this.getSourceFetchedAt() + ")";
    }

    /**
     * {@code EvidenceCandidateVO} 的链式构建器
     *
     * <p>全部字段均无默认值，未显式设置的字段保持 {@code null}
     */
    public static class EvidenceCandidateVOBuilder {
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

        /**
         * 创建空构建器，全部字段保持未设置状态
         */
        EvidenceCandidateVOBuilder() {
        }

        /**
         * 设置关联条目标识，覆盖此前取值
         * @param subjectId 关联的条目ID，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder subjectId(final Long subjectId) {
            this.subjectId = subjectId;
            return this;
        }

        /**
         * 设置来源数据的原始名称，覆盖此前取值
         * @param name 来源中的条目原始名称，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder name(final String name) {
            this.name = name;
            return this;
        }

        /**
         * 设置条目的中文名称，覆盖此前取值
         * @param nameCn 条目中文名，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder nameCn(final String nameCn) {
            this.nameCn = nameCn;
            return this;
        }

        /**
         * 设置业务类型或状态编码，覆盖此前取值
         * @param type 业务类型或状态编码，取值由所属接口约束，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder type(final Integer type) {
            this.type = type;
            return this;
        }

        /**
         * 设置是否包含 NSFW 内容，覆盖此前取值
         * @param nsfw 条目包含 NSFW 内容时为 {@code true}，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder nsfw(final Boolean nsfw) {
            this.nsfw = nsfw;
            return this;
        }

        /**
         * 设置来源事实是否仍活跃，覆盖此前取值
         * @param active 记录仍可供 Agent 使用时为 {@code true}，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder active(final Boolean active) {
            this.active = active;
            return this;
        }

        /**
         * 设置上游 Bangumi ID，覆盖此前取值
         * @param sourceId 上游 Bangumi 中的条目ID，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder sourceId(final Integer sourceId) {
            this.sourceId = sourceId;
            return this;
        }

        /**
         * 设置上游 Bangumi 详情 URL，覆盖此前取值
         * @param sourceUrl 上游 Bangumi 条目详情地址，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder sourceUrl(final String sourceUrl) {
            this.sourceUrl = sourceUrl;
            return this;
        }

        /**
         * 设置条目评分，覆盖此前取值
         * @param score 条目评分，取值遵循接口约定，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder score(final BigDecimal score) {
            this.score = score;
            return this;
        }

        /**
         * 设置候选结果排序名次，覆盖此前取值
         * @param rank 候选结果中的排序名次，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder rank(final Integer rank) {
            this.rank = rank;
            return this;
        }

        /**
         * 设置条目评分人数，覆盖此前取值
         * @param ratingTotal 为该条目打分的总人数，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder ratingTotal(final Integer ratingTotal) {
            this.ratingTotal = ratingTotal;
            return this;
        }

        /**
         * 设置条目收藏人数，覆盖此前取值
         * @param collectionTotal 收藏该条目的总人数，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder collectionTotal(final Integer collectionTotal) {
            this.collectionTotal = collectionTotal;
            return this;
        }

        /**
         * 设置条目的首播日期，覆盖此前取值
         * @param airDate 条目首播日期，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder airDate(final LocalDate airDate) {
            this.airDate = airDate;
            return this;
        }

        /**
         * 设置播出状态，覆盖此前取值
         * @param airStatus 由条目日期与剧集状态推导的播出状态，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder airStatus(final String airStatus) {
            this.airStatus = airStatus;
            return this;
        }

        /**
         * 设置条目的简介文本，覆盖此前取值
         * @param summary 条目简介，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder summary(final String summary) {
            this.summary = summary;
            return this;
        }

        /**
         * 设置条目的别名列表，覆盖此前取值
         * @param aliases 别名列表，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder aliases(final List<String> aliases) {
            this.aliases = aliases;
            return this;
        }

        /**
         * 设置条目关联的元标签列表，覆盖此前取值
         * @param metaTags 元标签列表，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder metaTags(final List<String> metaTags) {
            this.metaTags = metaTags;
            return this;
        }

        /**
         * 设置条目演职人员列表，覆盖此前取值
         * @param credits 演职人员列表，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder credits(final List<CreditItem> credits) {
            this.credits = credits;
            return this;
        }

        /**
         * 设置条目关联的角色列表，覆盖此前取值
         * @param characters 角色列表，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder characters(final List<CharacterItem> characters) {
            this.characters = characters;
            return this;
        }

        /**
         * 设置条目关联关系列表，覆盖此前取值
         * @param relations 关联关系列表，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder relations(final List<RelationItem> relations) {
            this.relations = relations;
            return this;
        }

        /**
         * 设置来源数据对应的时间点，覆盖此前取值
         * @param sourceTime 来源数据时间点，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder sourceTime(final LocalDateTime sourceTime) {
            this.sourceTime = sourceTime;
            return this;
        }

        /**
         * 设置来源抓取时间点，覆盖此前取值
         * @param sourceFetchedAt 新字段名的来源抓取时间点，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public EvidenceCandidateVO.EvidenceCandidateVOBuilder sourceFetchedAt(final LocalDateTime sourceFetchedAt) {
            this.sourceFetchedAt = sourceFetchedAt;
            return this;
        }

        /**
         * 构建证据视图
         * @return 携带当前构建器取值的证据视图
         */
        public EvidenceCandidateVO build() {
            return new EvidenceCandidateVO(this.subjectId, this.name, this.nameCn, this.type, this.nsfw, this.active, this.sourceId, this.sourceUrl, this.score, this.rank, this.ratingTotal, this.collectionTotal, this.airDate, this.airStatus, this.summary, this.aliases, this.metaTags, this.credits, this.characters, this.relations, this.sourceTime, this.sourceFetchedAt);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "EvidenceCandidateVO.EvidenceCandidateVOBuilder(subjectId=" + this.subjectId + ", name=" + this.name + ", nameCn=" + this.nameCn + ", type=" + this.type + ", nsfw=" + this.nsfw + ", active=" + this.active + ", sourceId=" + this.sourceId + ", sourceUrl=" + this.sourceUrl + ", score=" + this.score + ", rank=" + this.rank + ", ratingTotal=" + this.ratingTotal + ", collectionTotal=" + this.collectionTotal + ", airDate=" + this.airDate + ", airStatus=" + this.airStatus + ", summary=" + this.summary + ", aliases=" + this.aliases + ", metaTags=" + this.metaTags + ", credits=" + this.credits + ", characters=" + this.characters + ", relations=" + this.relations + ", sourceTime=" + this.sourceTime + ", sourceFetchedAt=" + this.sourceFetchedAt + ")";
        }
    }

    /** CreditItem 数据对象 */
    public static class CreditItem {

        /** 人物名称 */
        private String personName;
        /** 人员或角色在关系中的职务 */
        private String role;
        /** 实体之间的关系类型 */
        private String relation;

        /** 创建字段均为默认值的空演职人员项 */
        public CreditItem() {
        }

        /**
         * 创建携带全部字段的演职人员项
         * @param personName 人物名称，可为 {@code null}
         * @param role 人员在作品中的职务，可为 {@code null}
         * @param relation 实体之间的关系类型，可为 {@code null}
         */
        public CreditItem(final String personName, final String role, final String relation) {
            this.personName = personName;
            this.role = role;
            this.relation = relation;
        }

        /**
         * 创建构建器，用于链式组装演职人员项
         * @return 空的演职人员项构建器
         */
        public static CreditItemBuilder builder() {
            return new CreditItemBuilder();
        }

        /**
         * 获取人物名称
         * @return 演职人员姓名；未提供时为 {@code null}
         */
        public String getPersonName() {
            return this.personName;
        }

        /**
         * 获取人员在作品中的职务
         * @return 人员在关系中的职务；未提供时为 {@code null}
         */
        public String getRole() {
            return this.role;
        }

        /**
         * 获取实体之间的关系类型
         * @return 实体之间的关系类型；未提供时为 {@code null}
         */
        public String getRelation() {
            return this.relation;
        }

        /**
         * 替换人物名称
         * @param personName 演职人员姓名，可为 {@code null}
         */
        public void setPersonName(final String personName) {
            this.personName = personName;
        }

        /**
         * 替换人员在作品中的职务
         * @param role 人员在关系中的职务，可为 {@code null}
         */
        public void setRole(final String role) {
            this.role = role;
        }

        /**
         * 替换实体之间的关系类型
         * @param relation 实体之间的关系类型，可为 {@code null}
         */
        public void setRelation(final String relation) {
            this.relation = relation;
        }

        /**
         * 判断与另一对象是否相等，比较本类全部字段
         * @param o 待比较的对象
         * @return 类型与全部字段均相等时为 {@code true}
         */
        @Override
        public boolean equals(final Object o) {
            if (o == this) return true;
            if (!(o instanceof EvidenceCandidateVO.CreditItem)) return false;
            final EvidenceCandidateVO.CreditItem other = (EvidenceCandidateVO.CreditItem) o;
            if (!other.canEqual((Object) this)) return false;
            final Object thisPersonName = this.getPersonName();
            final Object otherPersonName = other.getPersonName();
            if (thisPersonName == null ? otherPersonName != null : !thisPersonName.equals(otherPersonName)) return false;
            final Object thisRole = this.getRole();
            final Object otherRole = other.getRole();
            if (thisRole == null ? otherRole != null : !thisRole.equals(otherRole)) return false;
            final Object thisRelation = this.getRelation();
            final Object otherRelation = other.getRelation();
            if (thisRelation == null ? otherRelation != null : !thisRelation.equals(otherRelation)) return false;
            return true;
        }

        /**
         * 判断另一对象是否可参与相等比较
         * @param other 待比较的对象
         * @return 与当前类型兼容时为 {@code true}
         */
        protected boolean canEqual(final Object other) {
            return other instanceof EvidenceCandidateVO.CreditItem;
        }

        /**
         * 基于本类全部字段计算哈希值
         * @return 与 {@link #equals(Object)} 一致的哈希值
         */
        @Override
        public int hashCode() {
            final int PRIME = 59;
            int result = 1;
            final Object hashPersonName = this.getPersonName();
            result = result * PRIME + (hashPersonName == null ? 43 : hashPersonName.hashCode());
            final Object hashRole = this.getRole();
            result = result * PRIME + (hashRole == null ? 43 : hashRole.hashCode());
            final Object hashRelation = this.getRelation();
            result = result * PRIME + (hashRelation == null ? 43 : hashRelation.hashCode());
            return result;
        }

        /**
         * 返回包含本类全部字段的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "EvidenceCandidateVO.CreditItem(personName=" + this.getPersonName() + ", role=" + this.getRole() + ", relation=" + this.getRelation() + ")";
        }

        /**
         * {@code CreditItem} 的链式构建器
         *
         * <p>全部字段均无默认值，未显式设置的字段保持 {@code null}
         */
        public static class CreditItemBuilder {
            /** 人物名称 */
            private String personName;
            /** 人员或角色在关系中的职务 */
            private String role;
            /** 实体之间的关系类型 */
            private String relation;

            /**
             * 创建空构建器，全部字段保持未设置状态
             */
            CreditItemBuilder() {
            }

            /**
             * 设置人物名称，覆盖此前取值
             * @param personName 演职人员姓名，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.CreditItem.CreditItemBuilder personName(final String personName) {
                this.personName = personName;
                return this;
            }

            /**
             * 设置人员在作品中的职务，覆盖此前取值
             * @param role 人员在关系中的职务，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.CreditItem.CreditItemBuilder role(final String role) {
                this.role = role;
                return this;
            }

            /**
             * 设置实体之间的关系类型，覆盖此前取值
             * @param relation 实体之间的关系类型，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.CreditItem.CreditItemBuilder relation(final String relation) {
                this.relation = relation;
                return this;
            }

            /**
             * 构建演职人员项
             * @return 携带当前构建器取值的演职人员项
             */
            public EvidenceCandidateVO.CreditItem build() {
                return new EvidenceCandidateVO.CreditItem(this.personName, this.role, this.relation);
            }

            /**
             * 返回包含构建器当前取值的字符串表示
             * @return 字段名与取值的文本
             */
            @Override
            public String toString() {
                return "EvidenceCandidateVO.CreditItem.CreditItemBuilder(personName=" + this.personName + ", role=" + this.role + ", relation=" + this.relation + ")";
            }
        }
    }

    /** CharacterItem 数据对象 */
    public static class CharacterItem {

        /** 角色名称 */
        private String characterName;
        /** 实体之间的关系类型 */
        private String relation;

        /** 创建字段均为默认值的空角色项 */
        public CharacterItem() {
        }

        /**
         * 创建携带全部字段的角色项
         * @param characterName 角色名称，可为 {@code null}
         * @param relation 实体之间的关系类型，可为 {@code null}
         */
        public CharacterItem(final String characterName, final String relation) {
            this.characterName = characterName;
            this.relation = relation;
        }

        /**
         * 创建构建器，用于链式组装角色项
         * @return 空的角色项构建器
         */
        public static CharacterItemBuilder builder() {
            return new CharacterItemBuilder();
        }

        /**
         * 获取角色名称
         * @return 角色名称；未提供时为 {@code null}
         */
        public String getCharacterName() {
            return this.characterName;
        }

        /**
         * 获取实体之间的关系类型
         * @return 实体之间的关系类型；未提供时为 {@code null}
         */
        public String getRelation() {
            return this.relation;
        }

        /**
         * 替换角色名称
         * @param characterName 角色名称，可为 {@code null}
         */
        public void setCharacterName(final String characterName) {
            this.characterName = characterName;
        }

        /**
         * 替换实体之间的关系类型
         * @param relation 实体之间的关系类型，可为 {@code null}
         */
        public void setRelation(final String relation) {
            this.relation = relation;
        }

        /**
         * 判断与另一对象是否相等，比较本类全部字段
         * @param o 待比较的对象
         * @return 类型与全部字段均相等时为 {@code true}
         */
        @Override
        public boolean equals(final Object o) {
            if (o == this) return true;
            if (!(o instanceof EvidenceCandidateVO.CharacterItem)) return false;
            final EvidenceCandidateVO.CharacterItem other = (EvidenceCandidateVO.CharacterItem) o;
            if (!other.canEqual((Object) this)) return false;
            final Object thisCharacterName = this.getCharacterName();
            final Object otherCharacterName = other.getCharacterName();
            if (thisCharacterName == null ? otherCharacterName != null : !thisCharacterName.equals(otherCharacterName)) return false;
            final Object thisRelation = this.getRelation();
            final Object otherRelation = other.getRelation();
            if (thisRelation == null ? otherRelation != null : !thisRelation.equals(otherRelation)) return false;
            return true;
        }

        /**
         * 判断另一对象是否可参与相等比较
         * @param other 待比较的对象
         * @return 与当前类型兼容时为 {@code true}
         */
        protected boolean canEqual(final Object other) {
            return other instanceof EvidenceCandidateVO.CharacterItem;
        }

        /**
         * 基于本类全部字段计算哈希值
         * @return 与 {@link #equals(Object)} 一致的哈希值
         */
        @Override
        public int hashCode() {
            final int PRIME = 59;
            int result = 1;
            final Object hashCharacterName = this.getCharacterName();
            result = result * PRIME + (hashCharacterName == null ? 43 : hashCharacterName.hashCode());
            final Object hashRelation = this.getRelation();
            result = result * PRIME + (hashRelation == null ? 43 : hashRelation.hashCode());
            return result;
        }

        /**
         * 返回包含本类全部字段的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "EvidenceCandidateVO.CharacterItem(characterName=" + this.getCharacterName() + ", relation=" + this.getRelation() + ")";
        }

        /**
         * {@code CharacterItem} 的链式构建器
         *
         * <p>全部字段均无默认值，未显式设置的字段保持 {@code null}
         */
        public static class CharacterItemBuilder {
            /** 角色名称 */
            private String characterName;
            /** 实体之间的关系类型 */
            private String relation;

            /**
             * 创建空构建器，全部字段保持未设置状态
             */
            CharacterItemBuilder() {
            }

            /**
             * 设置角色名称，覆盖此前取值
             * @param characterName 角色名称，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.CharacterItem.CharacterItemBuilder characterName(final String characterName) {
                this.characterName = characterName;
                return this;
            }

            /**
             * 设置实体之间的关系类型，覆盖此前取值
             * @param relation 实体之间的关系类型，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.CharacterItem.CharacterItemBuilder relation(final String relation) {
                this.relation = relation;
                return this;
            }

            /**
             * 构建角色项
             * @return 携带当前构建器取值的角色项
             */
            public EvidenceCandidateVO.CharacterItem build() {
                return new EvidenceCandidateVO.CharacterItem(this.characterName, this.relation);
            }

            /**
             * 返回包含构建器当前取值的字符串表示
             * @return 字段名与取值的文本
             */
            @Override
            public String toString() {
                return "EvidenceCandidateVO.CharacterItem.CharacterItemBuilder(characterName=" + this.characterName + ", relation=" + this.relation + ")";
            }
        }
    }

    /** RelationItem 数据对象 */
    public static class RelationItem {

        /** 关联条目标识 */
        private Long relatedSubjectId;
        /** 关联条目的原始名称 */
        private String relatedSubjectName;
        /** 关联条目的中文名称 */
        private String relatedSubjectNameCn;
        /** 实体之间的关系类型 */
        private String relation;

        /** 创建字段均为默认值的空关联关系项 */
        public RelationItem() {
        }

        /**
         * 创建携带全部字段的关联关系项
         * @param relatedSubjectId 关联条目标识，可为 {@code null}
         * @param relatedSubjectName 关联条目的原始名称，可为 {@code null}
         * @param relatedSubjectNameCn 关联条目的中文名称，可为 {@code null}
         * @param relation 实体之间的关系类型，可为 {@code null}
         */
        public RelationItem(final Long relatedSubjectId, final String relatedSubjectName, final String relatedSubjectNameCn, final String relation) {
            this.relatedSubjectId = relatedSubjectId;
            this.relatedSubjectName = relatedSubjectName;
            this.relatedSubjectNameCn = relatedSubjectNameCn;
            this.relation = relation;
        }

        /**
         * 创建构建器，用于链式组装关联关系项
         * @return 空的关联关系项构建器
         */
        public static RelationItemBuilder builder() {
            return new RelationItemBuilder();
        }

        /**
         * 获取关联条目标识
         * @return 关联条目的ID；未提供时为 {@code null}
         */
        public Long getRelatedSubjectId() {
            return this.relatedSubjectId;
        }

        /**
         * 获取关联条目的原始名称
         * @return 关联条目的原始名称；未提供时为 {@code null}
         */
        public String getRelatedSubjectName() {
            return this.relatedSubjectName;
        }

        /**
         * 获取关联条目的中文名称
         * @return 关联条目的中文名称；未提供时为 {@code null}
         */
        public String getRelatedSubjectNameCn() {
            return this.relatedSubjectNameCn;
        }

        /**
         * 获取实体之间的关系类型
         * @return 实体之间的关系类型；未提供时为 {@code null}
         */
        public String getRelation() {
            return this.relation;
        }

        /**
         * 替换关联条目标识
         * @param relatedSubjectId 关联条目的ID，可为 {@code null}
         */
        public void setRelatedSubjectId(final Long relatedSubjectId) {
            this.relatedSubjectId = relatedSubjectId;
        }

        /**
         * 替换关联条目的原始名称
         * @param relatedSubjectName 关联条目的原始名称，可为 {@code null}
         */
        public void setRelatedSubjectName(final String relatedSubjectName) {
            this.relatedSubjectName = relatedSubjectName;
        }

        /**
         * 替换关联条目的中文名称
         * @param relatedSubjectNameCn 关联条目的中文名称，可为 {@code null}
         */
        public void setRelatedSubjectNameCn(final String relatedSubjectNameCn) {
            this.relatedSubjectNameCn = relatedSubjectNameCn;
        }

        /**
         * 替换实体之间的关系类型
         * @param relation 实体之间的关系类型，可为 {@code null}
         */
        public void setRelation(final String relation) {
            this.relation = relation;
        }

        /**
         * 判断与另一对象是否相等，比较本类全部字段
         * @param o 待比较的对象
         * @return 类型与全部字段均相等时为 {@code true}
         */
        @Override
        public boolean equals(final Object o) {
            if (o == this) return true;
            if (!(o instanceof EvidenceCandidateVO.RelationItem)) return false;
            final EvidenceCandidateVO.RelationItem other = (EvidenceCandidateVO.RelationItem) o;
            if (!other.canEqual((Object) this)) return false;
            final Object thisRelatedSubjectId = this.getRelatedSubjectId();
            final Object otherRelatedSubjectId = other.getRelatedSubjectId();
            if (thisRelatedSubjectId == null ? otherRelatedSubjectId != null : !thisRelatedSubjectId.equals(otherRelatedSubjectId)) return false;
            final Object thisRelatedSubjectName = this.getRelatedSubjectName();
            final Object otherRelatedSubjectName = other.getRelatedSubjectName();
            if (thisRelatedSubjectName == null ? otherRelatedSubjectName != null : !thisRelatedSubjectName.equals(otherRelatedSubjectName)) return false;
            final Object thisRelatedSubjectNameCn = this.getRelatedSubjectNameCn();
            final Object otherRelatedSubjectNameCn = other.getRelatedSubjectNameCn();
            if (thisRelatedSubjectNameCn == null ? otherRelatedSubjectNameCn != null : !thisRelatedSubjectNameCn.equals(otherRelatedSubjectNameCn)) return false;
            final Object thisRelation = this.getRelation();
            final Object otherRelation = other.getRelation();
            if (thisRelation == null ? otherRelation != null : !thisRelation.equals(otherRelation)) return false;
            return true;
        }

        /**
         * 判断另一对象是否可参与相等比较
         * @param other 待比较的对象
         * @return 与当前类型兼容时为 {@code true}
         */
        protected boolean canEqual(final Object other) {
            return other instanceof EvidenceCandidateVO.RelationItem;
        }

        /**
         * 基于本类全部字段计算哈希值
         * @return 与 {@link #equals(Object)} 一致的哈希值
         */
        @Override
        public int hashCode() {
            final int PRIME = 59;
            int result = 1;
            final Object hashRelatedSubjectId = this.getRelatedSubjectId();
            result = result * PRIME + (hashRelatedSubjectId == null ? 43 : hashRelatedSubjectId.hashCode());
            final Object hashRelatedSubjectName = this.getRelatedSubjectName();
            result = result * PRIME + (hashRelatedSubjectName == null ? 43 : hashRelatedSubjectName.hashCode());
            final Object hashRelatedSubjectNameCn = this.getRelatedSubjectNameCn();
            result = result * PRIME + (hashRelatedSubjectNameCn == null ? 43 : hashRelatedSubjectNameCn.hashCode());
            final Object hashRelation = this.getRelation();
            result = result * PRIME + (hashRelation == null ? 43 : hashRelation.hashCode());
            return result;
        }

        /**
         * 返回包含本类全部字段的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "EvidenceCandidateVO.RelationItem(relatedSubjectId=" + this.getRelatedSubjectId() + ", relatedSubjectName=" + this.getRelatedSubjectName() + ", relatedSubjectNameCn=" + this.getRelatedSubjectNameCn() + ", relation=" + this.getRelation() + ")";
        }

        /**
         * {@code RelationItem} 的链式构建器
         *
         * <p>全部字段均无默认值，未显式设置的字段保持 {@code null}
         */
        public static class RelationItemBuilder {
            /** 关联条目标识 */
            private Long relatedSubjectId;
            /** 关联条目的原始名称 */
            private String relatedSubjectName;
            /** 关联条目的中文名称 */
            private String relatedSubjectNameCn;
            /** 实体之间的关系类型 */
            private String relation;

            /**
             * 创建空构建器，全部字段保持未设置状态
             */
            RelationItemBuilder() {
            }

            /**
             * 设置关联条目标识，覆盖此前取值
             * @param relatedSubjectId 关联条目的ID，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.RelationItem.RelationItemBuilder relatedSubjectId(final Long relatedSubjectId) {
                this.relatedSubjectId = relatedSubjectId;
                return this;
            }

            /**
             * 设置关联条目的原始名称，覆盖此前取值
             * @param relatedSubjectName 关联条目的原始名称，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.RelationItem.RelationItemBuilder relatedSubjectName(final String relatedSubjectName) {
                this.relatedSubjectName = relatedSubjectName;
                return this;
            }

            /**
             * 设置关联条目的中文名称，覆盖此前取值
             * @param relatedSubjectNameCn 关联条目的中文名称，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.RelationItem.RelationItemBuilder relatedSubjectNameCn(final String relatedSubjectNameCn) {
                this.relatedSubjectNameCn = relatedSubjectNameCn;
                return this;
            }

            /**
             * 设置实体之间的关系类型，覆盖此前取值
             * @param relation 实体之间的关系类型，可为 {@code null}
             * @return {@code this}，用于链式调用
             */
            public EvidenceCandidateVO.RelationItem.RelationItemBuilder relation(final String relation) {
                this.relation = relation;
                return this;
            }

            /**
             * 构建关联关系项
             * @return 携带当前构建器取值的关联关系项
             */
            public EvidenceCandidateVO.RelationItem build() {
                return new EvidenceCandidateVO.RelationItem(this.relatedSubjectId, this.relatedSubjectName, this.relatedSubjectNameCn, this.relation);
            }

            /**
             * 返回包含构建器当前取值的字符串表示
             * @return 字段名与取值的文本
             */
            @Override
            public String toString() {
                return "EvidenceCandidateVO.RelationItem.RelationItemBuilder(relatedSubjectId=" + this.relatedSubjectId + ", relatedSubjectName=" + this.relatedSubjectName + ", relatedSubjectNameCn=" + this.relatedSubjectNameCn + ", relation=" + this.relation + ")";
            }
        }
    }
}
