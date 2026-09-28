package top.zhaizz.client.model;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 条目基础数据行
 */
public class EvidenceSubjectRow {
    /**
     * 关联条目标识
     */
    private Long subjectId;
    /**
     * 来源数据的原始名称
     */
    private String name;
    /**
     * 条目的中文名称
     */
    private String nameCn;
    /**
     * 业务类型或状态编码
     */
    private Integer type;
    /**
     * 条目是否包含 NSFW 内容
     */
    private Boolean nsfw;
    /**
     * 来源记录是否仍有效
     */
    private Boolean active;
    /**
     * 来源系统中的记录标识
     */
    private Integer sourceId;
    /**
     * 来源记录的原始链接
     */
    private String sourceUrl;
    /**
     * 条目评分
     */
    private BigDecimal score;
    /**
     * 候选结果排序名次
     */
    private Integer rank;
    /**
     * 条目评分人数
     */
    private Integer ratingTotal;
    /**
     * 条目收藏人数
     */
    private Integer collectionTotal;
    /**
     * 条目的首播日期
     */
    private LocalDate airDate;
    /**
     * 条目的播出状态
     */
    private String airStatus;
    /**
     * 条目的简介文本
     */
    private String summary;
    /**
     * 从来源系统抓取数据的时间
     */
    private LocalDateTime sourceFetchedAt;

    /** 创建字段均为默认值的空条目行，供结果映射使用 */
    public EvidenceSubjectRow() {
    }

    /**
     * 获取关联条目标识
     * @return 条目主键，未设置时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取来源数据的原始名称
     * @return 条目的原始语言名称，未设置时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取条目的中文名称
     * @return 条目中文名称，未设置时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取业务类型或状态编码
     * @return 条目类型编码，未设置时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取条目是否包含 NSFW 内容
     * @return 包含 NSFW 内容时为 {@code true}，未设置时为 {@code null}
     */
    public Boolean getNsfw() {
        return this.nsfw;
    }

    /**
     * 获取来源记录是否仍有效
     * @return 来源记录有效时为 {@code true}，未设置时为 {@code null}
     */
    public Boolean getActive() {
        return this.active;
    }

    /**
     * 获取来源系统中的记录标识
     * @return 上游来源的条目 ID，未设置时为 {@code null}
     */
    public Integer getSourceId() {
        return this.sourceId;
    }

    /**
     * 获取来源记录的原始链接
     * @return 上游来源链接，未设置时为 {@code null}
     */
    public String getSourceUrl() {
        return this.sourceUrl;
    }

    /**
     * 获取条目评分
     * @return 来源评分值，未设置时为 {@code null}
     */
    public BigDecimal getScore() {
        return this.score;
    }

    /**
     * 获取候选结果排序名次
     * @return 候选排序名次，未设置时为 {@code null}
     */
    public Integer getRank() {
        return this.rank;
    }

    /**
     * 获取条目评分人数
     * @return 参与评分的总人数，未设置时为 {@code null}
     */
    public Integer getRatingTotal() {
        return this.ratingTotal;
    }

    /**
     * 获取条目收藏人数
     * @return 收藏该条目的总人数，未设置时为 {@code null}
     */
    public Integer getCollectionTotal() {
        return this.collectionTotal;
    }

    /**
     * 获取条目的首播日期
     * @return 首播日期，未设置时为 {@code null}
     */
    public LocalDate getAirDate() {
        return this.airDate;
    }

    /**
     * 获取条目的播出状态
     * @return 播出状态文本，未设置时为 {@code null}
     */
    public String getAirStatus() {
        return this.airStatus;
    }

    /**
     * 获取条目的简介文本
     * @return 条目简介，未设置时为 {@code null}
     */
    public String getSummary() {
        return this.summary;
    }

    /**
     * 获取从来源系统抓取数据的时间
     * @return 来源数据抓取时刻，未设置时为 {@code null}
     */
    public LocalDateTime getSourceFetchedAt() {
        return this.sourceFetchedAt;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 新的条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换来源数据的原始名称
     * @param name 新的条目原始语言名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换条目的中文名称
     * @param nameCn 新的条目中文名称，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换业务类型或状态编码
     * @param type 新的条目类型编码，可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换条目是否包含 NSFW 内容
     * @param nsfw 包含 NSFW 内容时为 {@code true}，可为 {@code null}
     */
    public void setNsfw(final Boolean nsfw) {
        this.nsfw = nsfw;
    }

    /**
     * 替换来源记录是否仍有效
     * @param active 来源记录有效时为 {@code true}，可为 {@code null}
     */
    public void setActive(final Boolean active) {
        this.active = active;
    }

    /**
     * 替换来源系统中的记录标识
     * @param sourceId 新的上游来源条目 ID，可为 {@code null}
     */
    public void setSourceId(final Integer sourceId) {
        this.sourceId = sourceId;
    }

    /**
     * 替换来源记录的原始链接
     * @param sourceUrl 新的上游来源链接，可为 {@code null}
     */
    public void setSourceUrl(final String sourceUrl) {
        this.sourceUrl = sourceUrl;
    }

    /**
     * 替换条目评分
     * @param score 新的来源评分值，可为 {@code null}
     */
    public void setScore(final BigDecimal score) {
        this.score = score;
    }

    /**
     * 替换候选结果排序名次
     * @param rank 新的候选排序名次，可为 {@code null}
     */
    public void setRank(final Integer rank) {
        this.rank = rank;
    }

    /**
     * 替换条目评分人数
     * @param ratingTotal 新的参与评分总人数，可为 {@code null}
     */
    public void setRatingTotal(final Integer ratingTotal) {
        this.ratingTotal = ratingTotal;
    }

    /**
     * 替换条目收藏人数
     * @param collectionTotal 新的收藏总人数，可为 {@code null}
     */
    public void setCollectionTotal(final Integer collectionTotal) {
        this.collectionTotal = collectionTotal;
    }

    /**
     * 替换条目的首播日期
     * @param airDate 新的首播日期，可为 {@code null}
     */
    public void setAirDate(final LocalDate airDate) {
        this.airDate = airDate;
    }

    /**
     * 替换条目的播出状态
     * @param airStatus 新的播出状态文本，可为 {@code null}
     */
    public void setAirStatus(final String airStatus) {
        this.airStatus = airStatus;
    }

    /**
     * 替换条目的简介文本
     * @param summary 新的条目简介，可为 {@code null}
     */
    public void setSummary(final String summary) {
        this.summary = summary;
    }

    /**
     * 替换从来源系统抓取数据的时间
     * @param sourceFetchedAt 新的来源数据抓取时刻，可为 {@code null}
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
        if (!(o instanceof EvidenceSubjectRow)) return false;
        final EvidenceSubjectRow other = (EvidenceSubjectRow) o;
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
        return other instanceof EvidenceSubjectRow;
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
        return "EvidenceSubjectRow(subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", type=" + this.getType() + ", nsfw=" + this.getNsfw() + ", active=" + this.getActive() + ", sourceId=" + this.getSourceId() + ", sourceUrl=" + this.getSourceUrl() + ", score=" + this.getScore() + ", rank=" + this.getRank() + ", ratingTotal=" + this.getRatingTotal() + ", collectionTotal=" + this.getCollectionTotal() + ", airDate=" + this.getAirDate() + ", airStatus=" + this.getAirStatus() + ", summary=" + this.getSummary() + ", sourceFetchedAt=" + this.getSourceFetchedAt() + ")";
    }
}
