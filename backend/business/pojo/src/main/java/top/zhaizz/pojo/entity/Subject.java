package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 动漫条目实体
 */
@TableName("subject")
public class Subject {

    /** 条目ID */
    private Long id;                    // 条目ID

    /** Bangumi API 条目ID */
    private Integer bangumiId;          // Bangumi API 条目ID

    /** 日文/英文名 */
    private String name;                // 日文/英文名

    /** 中文名 */
    private String nameCn;              // 中文名

    /** 简介/描述 */
    private String summary;             // 简介/描述

    /** 条目类型: 2=动画（本项目仅使用动画类型） */
    private Integer type;               // 条目类型: 2=动画（本项目仅使用动画类型）

    /** 总集数 */
    private Integer eps;                // 总集数

    /** 总卷数 */
    private Integer volumes;            // 总卷数

    /** 播出日期 */
    private LocalDate airDate;          // 播出日期

    /** 播出星期（0=周日, 1=周一 ... 6=周六） */
    private Integer airWeekday;         // 播出星期（0=周日, 1=周一 ... 6=周六）

    /** 封面图URL */
    private String image;               // 封面图URL

    /** Bangumi 评分（0.0~10.0） */
    private BigDecimal score;           // Bangumi 评分（0.0~10.0）

    /** Bangumi 排名 */
    @TableField("`rank`")
    private Integer rank;               // Bangumi 排名

    /** 收藏数 */
    private Integer collectionTotal;    // 收藏数

    /** 评分总人数 */
    private Integer ratingTotal;        // 评分总人数

    /** 各评分人数 JSON */
    private String ratingCountJson;     // 各评分人数 JSON

    /** 想看人数 */
    private Integer collectionWish;     // 想看人数

    /** 看过人数 */
    private Integer collectionCollect;  // 看过人数

    /** 在看人数 */
    private Integer collectionDoing;    // 在看人数

    /** 搁置人数 */
    private Integer collectionOnHold;   // 搁置人数

    /** 抛弃人数 */
    private Integer collectionDropped;  // 抛弃人数

    /** 原始封面 URL */
    private String imageSourceUrl;      // 原始封面 URL

    /** 封面存储状态 */
    private String imageStorageStatus;  // 封面存储状态

    /** 最近封面检查时间 */
    private LocalDateTime imageCheckedAt; // 最近封面检查时间

    /** 本系统最近成功抓取源详情时间 */
    private LocalDateTime sourceFetchedAt; // 本系统最近成功抓取源详情时间

    /** 是否 NSFW: 0=否, 1=是 */
    private Boolean nsfw;               // 是否 NSFW: 0=否, 1=是

    /** 导入状态: 0=待导入, 1=已导入 */
    private Integer importStatus;       // 导入状态: 0=待导入, 1=已导入

    /** 最近导入时间 */
    private LocalDateTime lastImportedAt; // 最近导入时间

    /** 创建时间 */
    private LocalDateTime createdAt;    // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;    // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public Subject() {
    }

    /**
     * 获取条目ID
     * @return 条目ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取Bangumi API 条目ID
     * @return Bangumi API 条目ID；未持久化或未提供时为 {@code null}
     */
    public Integer getBangumiId() {
        return this.bangumiId;
    }

    /**
     * 获取日文/英文名
     * @return 日文/英文名；未持久化或未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取中文名
     * @return 中文名；未持久化或未提供时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取简介/描述
     * @return 简介/描述；未持久化或未提供时为 {@code null}
     */
    public String getSummary() {
        return this.summary;
    }

    /**
     * 获取条目类型: 2=动画（本项目仅使用动画类型）
     * @return 条目类型: 2=动画（本项目仅使用动画类型）；未持久化或未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取总集数
     * @return 总集数；未持久化或未提供时为 {@code null}
     */
    public Integer getEps() {
        return this.eps;
    }

    /**
     * 获取总卷数
     * @return 总卷数；未持久化或未提供时为 {@code null}
     */
    public Integer getVolumes() {
        return this.volumes;
    }

    /**
     * 获取播出日期
     * @return 播出日期；未持久化或未提供时为 {@code null}
     */
    public LocalDate getAirDate() {
        return this.airDate;
    }

    /**
     * 获取播出星期（0=周日, 1=周一 ... 6=周六）
     * @return 播出星期（0=周日, 1=周一 ... 6=周六）；未持久化或未提供时为 {@code null}
     */
    public Integer getAirWeekday() {
        return this.airWeekday;
    }

    /**
     * 获取封面图URL
     * @return 封面图URL；未持久化或未提供时为 {@code null}
     */
    public String getImage() {
        return this.image;
    }

    /**
     * 获取Bangumi 评分（0.0~10.0）
     * @return Bangumi 评分（0.0~10.0）；未持久化或未提供时为 {@code null}
     */
    public BigDecimal getScore() {
        return this.score;
    }

    /**
     * 获取Bangumi 排名
     * @return Bangumi 排名；未持久化或未提供时为 {@code null}
     */
    public Integer getRank() {
        return this.rank;
    }

    /**
     * 获取收藏数
     * @return 收藏数；未持久化或未提供时为 {@code null}
     */
    public Integer getCollectionTotal() {
        return this.collectionTotal;
    }

    /**
     * 获取评分总人数
     * @return 评分总人数；未持久化或未提供时为 {@code null}
     */
    public Integer getRatingTotal() {
        return this.ratingTotal;
    }

    /**
     * 获取各评分人数 JSON
     * @return 各评分人数 JSON；未持久化或未提供时为 {@code null}
     */
    public String getRatingCountJson() {
        return this.ratingCountJson;
    }

    /**
     * 获取想看人数
     * @return 想看人数；未持久化或未提供时为 {@code null}
     */
    public Integer getCollectionWish() {
        return this.collectionWish;
    }

    /**
     * 获取看过人数
     * @return 看过人数；未持久化或未提供时为 {@code null}
     */
    public Integer getCollectionCollect() {
        return this.collectionCollect;
    }

    /**
     * 获取在看人数
     * @return 在看人数；未持久化或未提供时为 {@code null}
     */
    public Integer getCollectionDoing() {
        return this.collectionDoing;
    }

    /**
     * 获取搁置人数
     * @return 搁置人数；未持久化或未提供时为 {@code null}
     */
    public Integer getCollectionOnHold() {
        return this.collectionOnHold;
    }

    /**
     * 获取抛弃人数
     * @return 抛弃人数；未持久化或未提供时为 {@code null}
     */
    public Integer getCollectionDropped() {
        return this.collectionDropped;
    }

    /**
     * 获取原始封面 URL
     * @return 原始封面 URL；未持久化或未提供时为 {@code null}
     */
    public String getImageSourceUrl() {
        return this.imageSourceUrl;
    }

    /**
     * 获取封面存储状态
     * @return 封面存储状态；未持久化或未提供时为 {@code null}
     */
    public String getImageStorageStatus() {
        return this.imageStorageStatus;
    }

    /**
     * 获取最近封面检查时间
     * @return 最近封面检查时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getImageCheckedAt() {
        return this.imageCheckedAt;
    }

    /**
     * 获取本系统最近成功抓取源详情时间
     * @return 本系统最近成功抓取源详情时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getSourceFetchedAt() {
        return this.sourceFetchedAt;
    }

    /**
     * 获取是否 NSFW: 0=否, 1=是
     * @return 是否 NSFW: 0=否, 1=是；未持久化或未提供时为 {@code null}
     */
    public Boolean getNsfw() {
        return this.nsfw;
    }

    /**
     * 获取导入状态: 0=待导入, 1=已导入
     * @return 导入状态: 0=待导入, 1=已导入；未持久化或未提供时为 {@code null}
     */
    public Integer getImportStatus() {
        return this.importStatus;
    }

    /**
     * 获取最近导入时间
     * @return 最近导入时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getLastImportedAt() {
        return this.lastImportedAt;
    }

    /**
     * 获取创建时间
     * @return 创建时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 获取更新时间
     * @return 更新时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getUpdatedAt() {
        return this.updatedAt;
    }

    /**
     * 替换条目ID
     * @param id 条目ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换Bangumi API 条目ID
     * @param bangumiId Bangumi API 条目ID，可为 {@code null}
     */
    public void setBangumiId(final Integer bangumiId) {
        this.bangumiId = bangumiId;
    }

    /**
     * 替换日文/英文名
     * @param name 日文/英文名，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换中文名
     * @param nameCn 中文名，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换简介/描述
     * @param summary 简介/描述，可为 {@code null}
     */
    public void setSummary(final String summary) {
        this.summary = summary;
    }

    /**
     * 替换条目类型: 2=动画（本项目仅使用动画类型）
     * @param type 条目类型: 2=动画（本项目仅使用动画类型），可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换总集数
     * @param eps 总集数，可为 {@code null}
     */
    public void setEps(final Integer eps) {
        this.eps = eps;
    }

    /**
     * 替换总卷数
     * @param volumes 总卷数，可为 {@code null}
     */
    public void setVolumes(final Integer volumes) {
        this.volumes = volumes;
    }

    /**
     * 替换播出日期
     * @param airDate 播出日期，可为 {@code null}
     */
    public void setAirDate(final LocalDate airDate) {
        this.airDate = airDate;
    }

    /**
     * 替换播出星期（0=周日, 1=周一 ... 6=周六）
     * @param airWeekday 播出星期（0=周日, 1=周一 ... 6=周六），可为 {@code null}
     */
    public void setAirWeekday(final Integer airWeekday) {
        this.airWeekday = airWeekday;
    }

    /**
     * 替换封面图URL
     * @param image 封面图URL，可为 {@code null}
     */
    public void setImage(final String image) {
        this.image = image;
    }

    /**
     * 替换Bangumi 评分（0.0~10.0）
     * @param score Bangumi 评分（0.0~10.0），可为 {@code null}
     */
    public void setScore(final BigDecimal score) {
        this.score = score;
    }

    /**
     * 替换Bangumi 排名
     * @param rank Bangumi 排名，可为 {@code null}
     */
    public void setRank(final Integer rank) {
        this.rank = rank;
    }

    /**
     * 替换收藏数
     * @param collectionTotal 收藏数，可为 {@code null}
     */
    public void setCollectionTotal(final Integer collectionTotal) {
        this.collectionTotal = collectionTotal;
    }

    /**
     * 替换评分总人数
     * @param ratingTotal 评分总人数，可为 {@code null}
     */
    public void setRatingTotal(final Integer ratingTotal) {
        this.ratingTotal = ratingTotal;
    }

    /**
     * 替换各评分人数 JSON
     * @param ratingCountJson 各评分人数 JSON，可为 {@code null}
     */
    public void setRatingCountJson(final String ratingCountJson) {
        this.ratingCountJson = ratingCountJson;
    }

    /**
     * 替换想看人数
     * @param collectionWish 想看人数，可为 {@code null}
     */
    public void setCollectionWish(final Integer collectionWish) {
        this.collectionWish = collectionWish;
    }

    /**
     * 替换看过人数
     * @param collectionCollect 看过人数，可为 {@code null}
     */
    public void setCollectionCollect(final Integer collectionCollect) {
        this.collectionCollect = collectionCollect;
    }

    /**
     * 替换在看人数
     * @param collectionDoing 在看人数，可为 {@code null}
     */
    public void setCollectionDoing(final Integer collectionDoing) {
        this.collectionDoing = collectionDoing;
    }

    /**
     * 替换搁置人数
     * @param collectionOnHold 搁置人数，可为 {@code null}
     */
    public void setCollectionOnHold(final Integer collectionOnHold) {
        this.collectionOnHold = collectionOnHold;
    }

    /**
     * 替换抛弃人数
     * @param collectionDropped 抛弃人数，可为 {@code null}
     */
    public void setCollectionDropped(final Integer collectionDropped) {
        this.collectionDropped = collectionDropped;
    }

    /**
     * 替换原始封面 URL
     * @param imageSourceUrl 原始封面 URL，可为 {@code null}
     */
    public void setImageSourceUrl(final String imageSourceUrl) {
        this.imageSourceUrl = imageSourceUrl;
    }

    /**
     * 替换封面存储状态
     * @param imageStorageStatus 封面存储状态，可为 {@code null}
     */
    public void setImageStorageStatus(final String imageStorageStatus) {
        this.imageStorageStatus = imageStorageStatus;
    }

    /**
     * 替换最近封面检查时间
     * @param imageCheckedAt 最近封面检查时间，可为 {@code null}
     */
    public void setImageCheckedAt(final LocalDateTime imageCheckedAt) {
        this.imageCheckedAt = imageCheckedAt;
    }

    /**
     * 替换本系统最近成功抓取源详情时间
     * @param sourceFetchedAt 本系统最近成功抓取源详情时间，可为 {@code null}
     */
    public void setSourceFetchedAt(final LocalDateTime sourceFetchedAt) {
        this.sourceFetchedAt = sourceFetchedAt;
    }

    /**
     * 替换是否 NSFW: 0=否, 1=是
     * @param nsfw 是否 NSFW: 0=否, 1=是，可为 {@code null}
     */
    public void setNsfw(final Boolean nsfw) {
        this.nsfw = nsfw;
    }

    /**
     * 替换导入状态: 0=待导入, 1=已导入
     * @param importStatus 导入状态: 0=待导入, 1=已导入，可为 {@code null}
     */
    public void setImportStatus(final Integer importStatus) {
        this.importStatus = importStatus;
    }

    /**
     * 替换最近导入时间
     * @param lastImportedAt 最近导入时间，可为 {@code null}
     */
    public void setLastImportedAt(final LocalDateTime lastImportedAt) {
        this.lastImportedAt = lastImportedAt;
    }

    /**
     * 替换创建时间
     * @param createdAt 创建时间，可为 {@code null}
     */
    public void setCreatedAt(final LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 替换更新时间
     * @param updatedAt 更新时间，可为 {@code null}
     */
    public void setUpdatedAt(final LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof Subject)) return false;
        final Subject other = (Subject) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisBangumiId = this.getBangumiId();
        final Object otherBangumiId = other.getBangumiId();
        if (thisBangumiId == null ? otherBangumiId != null : !thisBangumiId.equals(otherBangumiId)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisEps = this.getEps();
        final Object otherEps = other.getEps();
        if (thisEps == null ? otherEps != null : !thisEps.equals(otherEps)) return false;
        final Object thisVolumes = this.getVolumes();
        final Object otherVolumes = other.getVolumes();
        if (thisVolumes == null ? otherVolumes != null : !thisVolumes.equals(otherVolumes)) return false;
        final Object thisAirWeekday = this.getAirWeekday();
        final Object otherAirWeekday = other.getAirWeekday();
        if (thisAirWeekday == null ? otherAirWeekday != null : !thisAirWeekday.equals(otherAirWeekday)) return false;
        final Object thisRank = this.getRank();
        final Object otherRank = other.getRank();
        if (thisRank == null ? otherRank != null : !thisRank.equals(otherRank)) return false;
        final Object thisCollectionTotal = this.getCollectionTotal();
        final Object otherCollectionTotal = other.getCollectionTotal();
        if (thisCollectionTotal == null ? otherCollectionTotal != null : !thisCollectionTotal.equals(otherCollectionTotal)) return false;
        final Object thisRatingTotal = this.getRatingTotal();
        final Object otherRatingTotal = other.getRatingTotal();
        if (thisRatingTotal == null ? otherRatingTotal != null : !thisRatingTotal.equals(otherRatingTotal)) return false;
        final Object thisCollectionWish = this.getCollectionWish();
        final Object otherCollectionWish = other.getCollectionWish();
        if (thisCollectionWish == null ? otherCollectionWish != null : !thisCollectionWish.equals(otherCollectionWish)) return false;
        final Object thisCollectionCollect = this.getCollectionCollect();
        final Object otherCollectionCollect = other.getCollectionCollect();
        if (thisCollectionCollect == null ? otherCollectionCollect != null : !thisCollectionCollect.equals(otherCollectionCollect)) return false;
        final Object thisCollectionDoing = this.getCollectionDoing();
        final Object otherCollectionDoing = other.getCollectionDoing();
        if (thisCollectionDoing == null ? otherCollectionDoing != null : !thisCollectionDoing.equals(otherCollectionDoing)) return false;
        final Object thisCollectionOnHold = this.getCollectionOnHold();
        final Object otherCollectionOnHold = other.getCollectionOnHold();
        if (thisCollectionOnHold == null ? otherCollectionOnHold != null : !thisCollectionOnHold.equals(otherCollectionOnHold)) return false;
        final Object thisCollectionDropped = this.getCollectionDropped();
        final Object otherCollectionDropped = other.getCollectionDropped();
        if (thisCollectionDropped == null ? otherCollectionDropped != null : !thisCollectionDropped.equals(otherCollectionDropped)) return false;
        final Object thisNsfw = this.getNsfw();
        final Object otherNsfw = other.getNsfw();
        if (thisNsfw == null ? otherNsfw != null : !thisNsfw.equals(otherNsfw)) return false;
        final Object thisImportStatus = this.getImportStatus();
        final Object otherImportStatus = other.getImportStatus();
        if (thisImportStatus == null ? otherImportStatus != null : !thisImportStatus.equals(otherImportStatus)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisNameCn = this.getNameCn();
        final Object otherNameCn = other.getNameCn();
        if (thisNameCn == null ? otherNameCn != null : !thisNameCn.equals(otherNameCn)) return false;
        final Object thisSummary = this.getSummary();
        final Object otherSummary = other.getSummary();
        if (thisSummary == null ? otherSummary != null : !thisSummary.equals(otherSummary)) return false;
        final Object thisAirDate = this.getAirDate();
        final Object otherAirDate = other.getAirDate();
        if (thisAirDate == null ? otherAirDate != null : !thisAirDate.equals(otherAirDate)) return false;
        final Object thisImage = this.getImage();
        final Object otherImage = other.getImage();
        if (thisImage == null ? otherImage != null : !thisImage.equals(otherImage)) return false;
        final Object thisScore = this.getScore();
        final Object otherScore = other.getScore();
        if (thisScore == null ? otherScore != null : !thisScore.equals(otherScore)) return false;
        final Object thisRatingCountJson = this.getRatingCountJson();
        final Object otherRatingCountJson = other.getRatingCountJson();
        if (thisRatingCountJson == null ? otherRatingCountJson != null : !thisRatingCountJson.equals(otherRatingCountJson)) return false;
        final Object thisImageSourceUrl = this.getImageSourceUrl();
        final Object otherImageSourceUrl = other.getImageSourceUrl();
        if (thisImageSourceUrl == null ? otherImageSourceUrl != null : !thisImageSourceUrl.equals(otherImageSourceUrl)) return false;
        final Object thisImageStorageStatus = this.getImageStorageStatus();
        final Object otherImageStorageStatus = other.getImageStorageStatus();
        if (thisImageStorageStatus == null ? otherImageStorageStatus != null : !thisImageStorageStatus.equals(otherImageStorageStatus)) return false;
        final Object thisImageCheckedAt = this.getImageCheckedAt();
        final Object otherImageCheckedAt = other.getImageCheckedAt();
        if (thisImageCheckedAt == null ? otherImageCheckedAt != null : !thisImageCheckedAt.equals(otherImageCheckedAt)) return false;
        final Object thisSourceFetchedAt = this.getSourceFetchedAt();
        final Object otherSourceFetchedAt = other.getSourceFetchedAt();
        if (thisSourceFetchedAt == null ? otherSourceFetchedAt != null : !thisSourceFetchedAt.equals(otherSourceFetchedAt)) return false;
        final Object thisLastImportedAt = this.getLastImportedAt();
        final Object otherLastImportedAt = other.getLastImportedAt();
        if (thisLastImportedAt == null ? otherLastImportedAt != null : !thisLastImportedAt.equals(otherLastImportedAt)) return false;
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
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof Subject;
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
        final Object hashBangumiId = this.getBangumiId();
        result = result * PRIME + (hashBangumiId == null ? 43 : hashBangumiId.hashCode());
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashEps = this.getEps();
        result = result * PRIME + (hashEps == null ? 43 : hashEps.hashCode());
        final Object hashVolumes = this.getVolumes();
        result = result * PRIME + (hashVolumes == null ? 43 : hashVolumes.hashCode());
        final Object hashAirWeekday = this.getAirWeekday();
        result = result * PRIME + (hashAirWeekday == null ? 43 : hashAirWeekday.hashCode());
        final Object hashRank = this.getRank();
        result = result * PRIME + (hashRank == null ? 43 : hashRank.hashCode());
        final Object hashCollectionTotal = this.getCollectionTotal();
        result = result * PRIME + (hashCollectionTotal == null ? 43 : hashCollectionTotal.hashCode());
        final Object hashRatingTotal = this.getRatingTotal();
        result = result * PRIME + (hashRatingTotal == null ? 43 : hashRatingTotal.hashCode());
        final Object hashCollectionWish = this.getCollectionWish();
        result = result * PRIME + (hashCollectionWish == null ? 43 : hashCollectionWish.hashCode());
        final Object hashCollectionCollect = this.getCollectionCollect();
        result = result * PRIME + (hashCollectionCollect == null ? 43 : hashCollectionCollect.hashCode());
        final Object hashCollectionDoing = this.getCollectionDoing();
        result = result * PRIME + (hashCollectionDoing == null ? 43 : hashCollectionDoing.hashCode());
        final Object hashCollectionOnHold = this.getCollectionOnHold();
        result = result * PRIME + (hashCollectionOnHold == null ? 43 : hashCollectionOnHold.hashCode());
        final Object hashCollectionDropped = this.getCollectionDropped();
        result = result * PRIME + (hashCollectionDropped == null ? 43 : hashCollectionDropped.hashCode());
        final Object hashNsfw = this.getNsfw();
        result = result * PRIME + (hashNsfw == null ? 43 : hashNsfw.hashCode());
        final Object hashImportStatus = this.getImportStatus();
        result = result * PRIME + (hashImportStatus == null ? 43 : hashImportStatus.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashNameCn = this.getNameCn();
        result = result * PRIME + (hashNameCn == null ? 43 : hashNameCn.hashCode());
        final Object hashSummary = this.getSummary();
        result = result * PRIME + (hashSummary == null ? 43 : hashSummary.hashCode());
        final Object hashAirDate = this.getAirDate();
        result = result * PRIME + (hashAirDate == null ? 43 : hashAirDate.hashCode());
        final Object hashImage = this.getImage();
        result = result * PRIME + (hashImage == null ? 43 : hashImage.hashCode());
        final Object hashScore = this.getScore();
        result = result * PRIME + (hashScore == null ? 43 : hashScore.hashCode());
        final Object hashRatingCountJson = this.getRatingCountJson();
        result = result * PRIME + (hashRatingCountJson == null ? 43 : hashRatingCountJson.hashCode());
        final Object hashImageSourceUrl = this.getImageSourceUrl();
        result = result * PRIME + (hashImageSourceUrl == null ? 43 : hashImageSourceUrl.hashCode());
        final Object hashImageStorageStatus = this.getImageStorageStatus();
        result = result * PRIME + (hashImageStorageStatus == null ? 43 : hashImageStorageStatus.hashCode());
        final Object hashImageCheckedAt = this.getImageCheckedAt();
        result = result * PRIME + (hashImageCheckedAt == null ? 43 : hashImageCheckedAt.hashCode());
        final Object hashSourceFetchedAt = this.getSourceFetchedAt();
        result = result * PRIME + (hashSourceFetchedAt == null ? 43 : hashSourceFetchedAt.hashCode());
        final Object hashLastImportedAt = this.getLastImportedAt();
        result = result * PRIME + (hashLastImportedAt == null ? 43 : hashLastImportedAt.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        final Object hashUpdatedAt = this.getUpdatedAt();
        result = result * PRIME + (hashUpdatedAt == null ? 43 : hashUpdatedAt.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "Subject(id=" + this.getId() + ", bangumiId=" + this.getBangumiId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", summary=" + this.getSummary() + ", type=" + this.getType() + ", eps=" + this.getEps() + ", volumes=" + this.getVolumes() + ", airDate=" + this.getAirDate() + ", airWeekday=" + this.getAirWeekday() + ", image=" + this.getImage() + ", score=" + this.getScore() + ", rank=" + this.getRank() + ", collectionTotal=" + this.getCollectionTotal() + ", ratingTotal=" + this.getRatingTotal() + ", ratingCountJson=" + this.getRatingCountJson() + ", collectionWish=" + this.getCollectionWish() + ", collectionCollect=" + this.getCollectionCollect() + ", collectionDoing=" + this.getCollectionDoing() + ", collectionOnHold=" + this.getCollectionOnHold() + ", collectionDropped=" + this.getCollectionDropped() + ", imageSourceUrl=" + this.getImageSourceUrl() + ", imageStorageStatus=" + this.getImageStorageStatus() + ", imageCheckedAt=" + this.getImageCheckedAt() + ", sourceFetchedAt=" + this.getSourceFetchedAt() + ", nsfw=" + this.getNsfw() + ", importStatus=" + this.getImportStatus() + ", lastImportedAt=" + this.getLastImportedAt() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
