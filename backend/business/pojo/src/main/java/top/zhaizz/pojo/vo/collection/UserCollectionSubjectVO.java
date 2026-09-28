package top.zhaizz.pojo.vo.collection;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 用户收藏条目视图（扁平化 JOIN 结果）
 */
public class UserCollectionSubjectVO {

    /** 收藏ID */
    private Long id; // 收藏ID
    /** 用户ID */
    private Long userId; // 用户ID
    /** 条目ID */
    private Long subjectId; // 条目ID
    /** 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃 */
    private Integer type; // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    /** 评分（0~10, 0 表示未评分） */
    private Integer rate; // 评分（0~10, 0 表示未评分）
    /** 看到第几集 */
    private Integer epStatus; // 看到第几集
    /** 创建时间 */
    private LocalDateTime createdAt; // 创建时间
    /** 更新时间 */
    private LocalDateTime updatedAt; // 更新时间
    // subject 表的字段（扁平化 JOIN 结果）
    /** 日文/英文名 */
    private String name; // 日文/英文名
    /** 中文名 */
    private String nameCn; // 中文名
    /** 封面图URL */
    private String image; // 封面图URL
    /** Bangumi 评分 */
    private BigDecimal score; // Bangumi 评分
    /** 总集数 */
    private Integer eps; // 总集数
    /** 播出日期 */
    private LocalDate airDate; // 播出日期
    /** 播出星期 */
    private Integer airWeekday; // 播出星期
    /** 条目类型（2=动画） */
    private Integer subjectType;// 条目类型（2=动画）

    /** 创建字段均为默认值的空视图对象 */
    public UserCollectionSubjectVO() {
    }

    /**
     * 获取收藏ID
     * @return 用户收藏记录主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取用户ID
     * @return 收藏所属用户ID；未提供时为 {@code null}
     */
    public Long getUserId() {
        return this.userId;
    }

    /**
     * 获取条目ID
     * @return 被收藏的 Bangumi 条目ID；未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取收藏类型
     * @return 收藏类型：1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃；未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取评分
     * @return 用户评分（0~10，0 表示未评分）；未提供时为 {@code null}
     */
    public Integer getRate() {
        return this.rate;
    }

    /**
     * 获取看到第几集
     * @return 已观看到的剧集数；未提供时为 {@code null}
     */
    public Integer getEpStatus() {
        return this.epStatus;
    }

    /**
     * 获取创建时间
     * @return 收藏记录创建时间；未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 获取更新时间
     * @return 收藏记录最后更新时间；未提供时为 {@code null}
     */
    public LocalDateTime getUpdatedAt() {
        return this.updatedAt;
    }

    /**
     * 获取日文/英文名
     * @return 条目原始名称；未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取中文名
     * @return 条目中文名；未提供时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取封面图URL
     * @return 条目封面图地址；未提供时为 {@code null}
     */
    public String getImage() {
        return this.image;
    }

    /**
     * 获取 Bangumi 评分
     * @return 条目在 Bangumi 的评分；未提供时为 {@code null}
     */
    public BigDecimal getScore() {
        return this.score;
    }

    /**
     * 获取总集数
     * @return 条目的总集数；未提供时为 {@code null}
     */
    public Integer getEps() {
        return this.eps;
    }

    /**
     * 获取播出日期
     * @return 条目首播日期；未提供时为 {@code null}
     */
    public LocalDate getAirDate() {
        return this.airDate;
    }

    /**
     * 获取播出星期
     * @return 每周播出星期（数值表示）；未提供时为 {@code null}
     */
    public Integer getAirWeekday() {
        return this.airWeekday;
    }

    /**
     * 获取条目类型
     * @return 条目类型（2=动画）；未提供时为 {@code null}
     */
    public Integer getSubjectType() {
        return this.subjectType;
    }

    /**
     * 替换收藏ID
     * @param id 用户收藏记录主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换用户ID
     * @param userId 收藏所属用户ID，可为 {@code null}
     */
    public void setUserId(final Long userId) {
        this.userId = userId;
    }

    /**
     * 替换条目ID
     * @param subjectId 被收藏的 Bangumi 条目ID，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换收藏类型
     * @param type 收藏类型：1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃，可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换评分
     * @param rate 用户评分（0~10，0 表示未评分），可为 {@code null}
     */
    public void setRate(final Integer rate) {
        this.rate = rate;
    }

    /**
     * 替换看到第几集
     * @param epStatus 已观看到的剧集数，可为 {@code null}
     */
    public void setEpStatus(final Integer epStatus) {
        this.epStatus = epStatus;
    }

    /**
     * 替换创建时间
     * @param createdAt 收藏记录创建时间，可为 {@code null}
     */
    public void setCreatedAt(final LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 替换更新时间
     * @param updatedAt 收藏记录最后更新时间，可为 {@code null}
     */
    public void setUpdatedAt(final LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    /**
     * 替换日文/英文名
     * @param name 条目原始名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换中文名
     * @param nameCn 条目中文名，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换封面图URL
     * @param image 条目封面图地址，可为 {@code null}
     */
    public void setImage(final String image) {
        this.image = image;
    }

    /**
     * 替换 Bangumi 评分
     * @param score 条目在 Bangumi 的评分，可为 {@code null}
     */
    public void setScore(final BigDecimal score) {
        this.score = score;
    }

    /**
     * 替换总集数
     * @param eps 条目的总集数，可为 {@code null}
     */
    public void setEps(final Integer eps) {
        this.eps = eps;
    }

    /**
     * 替换播出日期
     * @param airDate 条目首播日期，可为 {@code null}
     */
    public void setAirDate(final LocalDate airDate) {
        this.airDate = airDate;
    }

    /**
     * 替换播出星期
     * @param airWeekday 每周播出星期（数值表示），可为 {@code null}
     */
    public void setAirWeekday(final Integer airWeekday) {
        this.airWeekday = airWeekday;
    }

    /**
     * 替换条目类型
     * @param subjectType 条目类型（2=动画），可为 {@code null}
     */
    public void setSubjectType(final Integer subjectType) {
        this.subjectType = subjectType;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof UserCollectionSubjectVO)) return false;
        final UserCollectionSubjectVO other = (UserCollectionSubjectVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisUserId = this.getUserId();
        final Object otherUserId = other.getUserId();
        if (thisUserId == null ? otherUserId != null : !thisUserId.equals(otherUserId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisRate = this.getRate();
        final Object otherRate = other.getRate();
        if (thisRate == null ? otherRate != null : !thisRate.equals(otherRate)) return false;
        final Object thisEpStatus = this.getEpStatus();
        final Object otherEpStatus = other.getEpStatus();
        if (thisEpStatus == null ? otherEpStatus != null : !thisEpStatus.equals(otherEpStatus)) return false;
        final Object thisEps = this.getEps();
        final Object otherEps = other.getEps();
        if (thisEps == null ? otherEps != null : !thisEps.equals(otherEps)) return false;
        final Object thisAirWeekday = this.getAirWeekday();
        final Object otherAirWeekday = other.getAirWeekday();
        if (thisAirWeekday == null ? otherAirWeekday != null : !thisAirWeekday.equals(otherAirWeekday)) return false;
        final Object thisSubjectType = this.getSubjectType();
        final Object otherSubjectType = other.getSubjectType();
        if (thisSubjectType == null ? otherSubjectType != null : !thisSubjectType.equals(otherSubjectType)) return false;
        final Object thisCreatedAt = this.getCreatedAt();
        final Object otherCreatedAt = other.getCreatedAt();
        if (thisCreatedAt == null ? otherCreatedAt != null : !thisCreatedAt.equals(otherCreatedAt)) return false;
        final Object thisUpdatedAt = this.getUpdatedAt();
        final Object otherUpdatedAt = other.getUpdatedAt();
        if (thisUpdatedAt == null ? otherUpdatedAt != null : !thisUpdatedAt.equals(otherUpdatedAt)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisNameCn = this.getNameCn();
        final Object otherNameCn = other.getNameCn();
        if (thisNameCn == null ? otherNameCn != null : !thisNameCn.equals(otherNameCn)) return false;
        final Object thisImage = this.getImage();
        final Object otherImage = other.getImage();
        if (thisImage == null ? otherImage != null : !thisImage.equals(otherImage)) return false;
        final Object thisScore = this.getScore();
        final Object otherScore = other.getScore();
        if (thisScore == null ? otherScore != null : !thisScore.equals(otherScore)) return false;
        final Object thisAirDate = this.getAirDate();
        final Object otherAirDate = other.getAirDate();
        if (thisAirDate == null ? otherAirDate != null : !thisAirDate.equals(otherAirDate)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof UserCollectionSubjectVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashId = this.getId();
        result = result * PRIME + (hashId == null ? 43 : hashId.hashCode());
        final Object hashUserId = this.getUserId();
        result = result * PRIME + (hashUserId == null ? 43 : hashUserId.hashCode());
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashRate = this.getRate();
        result = result * PRIME + (hashRate == null ? 43 : hashRate.hashCode());
        final Object hashEpStatus = this.getEpStatus();
        result = result * PRIME + (hashEpStatus == null ? 43 : hashEpStatus.hashCode());
        final Object hashEps = this.getEps();
        result = result * PRIME + (hashEps == null ? 43 : hashEps.hashCode());
        final Object hashAirWeekday = this.getAirWeekday();
        result = result * PRIME + (hashAirWeekday == null ? 43 : hashAirWeekday.hashCode());
        final Object hashSubjectType = this.getSubjectType();
        result = result * PRIME + (hashSubjectType == null ? 43 : hashSubjectType.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        final Object hashUpdatedAt = this.getUpdatedAt();
        result = result * PRIME + (hashUpdatedAt == null ? 43 : hashUpdatedAt.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashNameCn = this.getNameCn();
        result = result * PRIME + (hashNameCn == null ? 43 : hashNameCn.hashCode());
        final Object hashImage = this.getImage();
        result = result * PRIME + (hashImage == null ? 43 : hashImage.hashCode());
        final Object hashScore = this.getScore();
        result = result * PRIME + (hashScore == null ? 43 : hashScore.hashCode());
        final Object hashAirDate = this.getAirDate();
        result = result * PRIME + (hashAirDate == null ? 43 : hashAirDate.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "UserCollectionSubjectVO(id=" + this.getId() + ", userId=" + this.getUserId() + ", subjectId=" + this.getSubjectId() + ", type=" + this.getType() + ", rate=" + this.getRate() + ", epStatus=" + this.getEpStatus() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", image=" + this.getImage() + ", score=" + this.getScore() + ", eps=" + this.getEps() + ", airDate=" + this.getAirDate() + ", airWeekday=" + this.getAirWeekday() + ", subjectType=" + this.getSubjectType() + ")";
    }
}
