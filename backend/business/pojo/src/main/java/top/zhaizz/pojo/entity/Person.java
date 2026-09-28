package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;

/**
 * 人物/公司/组合实体
 */
@TableName("person")
public class Person {

    /** 人物ID */
    private Long id;                        // 人物ID

    /** Bangumi 人物ID */
    private Integer bangumiPersonId;        // Bangumi 人物ID

    /** 人物类型: PERSON=个人, COMPANY=公司, GROUP=组合（默认 PERSON） */
    private String personType;              // 人物类型: PERSON=个人, COMPANY=公司, GROUP=组合（默认 PERSON）

    /** 名称 */
    private String name;                    // 名称

    /** 简介 */
    private String summary;                 // 简介

    /** 职业 JSON（来自上游 infobox） */
    private String careerJson;              // 职业 JSON（来自上游 infobox）

    /** 完整 infobox JSON 快照 */
    private String infoboxJson;             // 完整 infobox JSON 快照

    /** 图片URL */
    private String image;                   // 图片URL

    /** 原始图片 URL */
    private String imageSourceUrl;          // 原始图片 URL

    /** 图片存储状态: PENDING/STORED/FAILED/ABSENT */
    private String imageStorageStatus;      // 图片存储状态: PENDING/STORED/FAILED/ABSENT

    /** 详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED */
    private String detailStatus;            // 详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED

    /** 来源数据哈希（用于变更检测） */
    private String sourceHash;              // 来源数据哈希（用于变更检测）

    /** 最近成功抓取源详情时间 */
    private LocalDateTime sourceFetchedAt;  // 最近成功抓取源详情时间

    /** 最近一次发现该实体的 import_record.id */
    private Long lastSeenImportId;          // 最近一次发现该实体的 import_record.id

    /** 上游是否仍然活跃: 0=已失效, 1=活跃 */
    private Boolean sourceActive;           // 上游是否仍然活跃: 0=已失效, 1=活跃

    /** 创建时间 */
    private LocalDateTime createdAt;        // 创建时间

    /** 更新时间 */
    private LocalDateTime updatedAt;        // 更新时间

    /** 创建各字段均为默认值的空实体 */
    public Person() {
    }

    /**
     * 获取人物ID
     * @return 人物ID；未持久化或未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取Bangumi 人物ID
     * @return Bangumi 人物ID；未持久化或未提供时为 {@code null}
     */
    public Integer getBangumiPersonId() {
        return this.bangumiPersonId;
    }

    /**
     * 获取人物类型: PERSON=个人, COMPANY=公司, GROUP=组合（默认 PERSON）
     * @return 人物类型: PERSON=个人, COMPANY=公司, GROUP=组合（默认 PERSON）；未持久化或未提供时为 {@code null}
     */
    public String getPersonType() {
        return this.personType;
    }

    /**
     * 获取名称
     * @return 名称；未持久化或未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取简介
     * @return 简介；未持久化或未提供时为 {@code null}
     */
    public String getSummary() {
        return this.summary;
    }

    /**
     * 获取职业 JSON（来自上游 infobox）
     * @return 职业 JSON（来自上游 infobox）；未持久化或未提供时为 {@code null}
     */
    public String getCareerJson() {
        return this.careerJson;
    }

    /**
     * 获取完整 infobox JSON 快照
     * @return 完整 infobox JSON 快照；未持久化或未提供时为 {@code null}
     */
    public String getInfoboxJson() {
        return this.infoboxJson;
    }

    /**
     * 获取图片URL
     * @return 图片URL；未持久化或未提供时为 {@code null}
     */
    public String getImage() {
        return this.image;
    }

    /**
     * 获取原始图片 URL
     * @return 原始图片 URL；未持久化或未提供时为 {@code null}
     */
    public String getImageSourceUrl() {
        return this.imageSourceUrl;
    }

    /**
     * 获取图片存储状态: PENDING/STORED/FAILED/ABSENT
     * @return 图片存储状态: PENDING/STORED/FAILED/ABSENT；未持久化或未提供时为 {@code null}
     */
    public String getImageStorageStatus() {
        return this.imageStorageStatus;
    }

    /**
     * 获取详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED
     * @return 详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED；未持久化或未提供时为 {@code null}
     */
    public String getDetailStatus() {
        return this.detailStatus;
    }

    /**
     * 获取来源数据哈希（用于变更检测）
     * @return 来源数据哈希（用于变更检测）；未持久化或未提供时为 {@code null}
     */
    public String getSourceHash() {
        return this.sourceHash;
    }

    /**
     * 获取最近成功抓取源详情时间
     * @return 最近成功抓取源详情时间；未持久化或未提供时为 {@code null}
     */
    public LocalDateTime getSourceFetchedAt() {
        return this.sourceFetchedAt;
    }

    /**
     * 获取最近一次发现该实体的 import_record.id
     * @return 最近一次发现该实体的 import_record.id；未持久化或未提供时为 {@code null}
     */
    public Long getLastSeenImportId() {
        return this.lastSeenImportId;
    }

    /**
     * 获取上游是否仍然活跃: 0=已失效, 1=活跃
     * @return 上游是否仍然活跃: 0=已失效, 1=活跃；未持久化或未提供时为 {@code null}
     */
    public Boolean getSourceActive() {
        return this.sourceActive;
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
     * 替换人物ID
     * @param id 人物ID，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换Bangumi 人物ID
     * @param bangumiPersonId Bangumi 人物ID，可为 {@code null}
     */
    public void setBangumiPersonId(final Integer bangumiPersonId) {
        this.bangumiPersonId = bangumiPersonId;
    }

    /**
     * 替换人物类型: PERSON=个人, COMPANY=公司, GROUP=组合（默认 PERSON）
     * @param personType 人物类型: PERSON=个人, COMPANY=公司, GROUP=组合（默认 PERSON），可为 {@code null}
     */
    public void setPersonType(final String personType) {
        this.personType = personType;
    }

    /**
     * 替换名称
     * @param name 名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换简介
     * @param summary 简介，可为 {@code null}
     */
    public void setSummary(final String summary) {
        this.summary = summary;
    }

    /**
     * 替换职业 JSON（来自上游 infobox）
     * @param careerJson 职业 JSON（来自上游 infobox），可为 {@code null}
     */
    public void setCareerJson(final String careerJson) {
        this.careerJson = careerJson;
    }

    /**
     * 替换完整 infobox JSON 快照
     * @param infoboxJson 完整 infobox JSON 快照，可为 {@code null}
     */
    public void setInfoboxJson(final String infoboxJson) {
        this.infoboxJson = infoboxJson;
    }

    /**
     * 替换图片URL
     * @param image 图片URL，可为 {@code null}
     */
    public void setImage(final String image) {
        this.image = image;
    }

    /**
     * 替换原始图片 URL
     * @param imageSourceUrl 原始图片 URL，可为 {@code null}
     */
    public void setImageSourceUrl(final String imageSourceUrl) {
        this.imageSourceUrl = imageSourceUrl;
    }

    /**
     * 替换图片存储状态: PENDING/STORED/FAILED/ABSENT
     * @param imageStorageStatus 图片存储状态: PENDING/STORED/FAILED/ABSENT，可为 {@code null}
     */
    public void setImageStorageStatus(final String imageStorageStatus) {
        this.imageStorageStatus = imageStorageStatus;
    }

    /**
     * 替换详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED
     * @param detailStatus 详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED，可为 {@code null}
     */
    public void setDetailStatus(final String detailStatus) {
        this.detailStatus = detailStatus;
    }

    /**
     * 替换来源数据哈希（用于变更检测）
     * @param sourceHash 来源数据哈希（用于变更检测），可为 {@code null}
     */
    public void setSourceHash(final String sourceHash) {
        this.sourceHash = sourceHash;
    }

    /**
     * 替换最近成功抓取源详情时间
     * @param sourceFetchedAt 最近成功抓取源详情时间，可为 {@code null}
     */
    public void setSourceFetchedAt(final LocalDateTime sourceFetchedAt) {
        this.sourceFetchedAt = sourceFetchedAt;
    }

    /**
     * 替换最近一次发现该实体的 import_record.id
     * @param lastSeenImportId 最近一次发现该实体的 import_record.id，可为 {@code null}
     */
    public void setLastSeenImportId(final Long lastSeenImportId) {
        this.lastSeenImportId = lastSeenImportId;
    }

    /**
     * 替换上游是否仍然活跃: 0=已失效, 1=活跃
     * @param sourceActive 上游是否仍然活跃: 0=已失效, 1=活跃，可为 {@code null}
     */
    public void setSourceActive(final Boolean sourceActive) {
        this.sourceActive = sourceActive;
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
        if (!(o instanceof Person)) return false;
        final Person other = (Person) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisBangumiPersonId = this.getBangumiPersonId();
        final Object otherBangumiPersonId = other.getBangumiPersonId();
        if (thisBangumiPersonId == null ? otherBangumiPersonId != null : !thisBangumiPersonId.equals(otherBangumiPersonId)) return false;
        final Object thisLastSeenImportId = this.getLastSeenImportId();
        final Object otherLastSeenImportId = other.getLastSeenImportId();
        if (thisLastSeenImportId == null ? otherLastSeenImportId != null : !thisLastSeenImportId.equals(otherLastSeenImportId)) return false;
        final Object thisSourceActive = this.getSourceActive();
        final Object otherSourceActive = other.getSourceActive();
        if (thisSourceActive == null ? otherSourceActive != null : !thisSourceActive.equals(otherSourceActive)) return false;
        final Object thisPersonType = this.getPersonType();
        final Object otherPersonType = other.getPersonType();
        if (thisPersonType == null ? otherPersonType != null : !thisPersonType.equals(otherPersonType)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisSummary = this.getSummary();
        final Object otherSummary = other.getSummary();
        if (thisSummary == null ? otherSummary != null : !thisSummary.equals(otherSummary)) return false;
        final Object thisCareerJson = this.getCareerJson();
        final Object otherCareerJson = other.getCareerJson();
        if (thisCareerJson == null ? otherCareerJson != null : !thisCareerJson.equals(otherCareerJson)) return false;
        final Object thisInfoboxJson = this.getInfoboxJson();
        final Object otherInfoboxJson = other.getInfoboxJson();
        if (thisInfoboxJson == null ? otherInfoboxJson != null : !thisInfoboxJson.equals(otherInfoboxJson)) return false;
        final Object thisImage = this.getImage();
        final Object otherImage = other.getImage();
        if (thisImage == null ? otherImage != null : !thisImage.equals(otherImage)) return false;
        final Object thisImageSourceUrl = this.getImageSourceUrl();
        final Object otherImageSourceUrl = other.getImageSourceUrl();
        if (thisImageSourceUrl == null ? otherImageSourceUrl != null : !thisImageSourceUrl.equals(otherImageSourceUrl)) return false;
        final Object thisImageStorageStatus = this.getImageStorageStatus();
        final Object otherImageStorageStatus = other.getImageStorageStatus();
        if (thisImageStorageStatus == null ? otherImageStorageStatus != null : !thisImageStorageStatus.equals(otherImageStorageStatus)) return false;
        final Object thisDetailStatus = this.getDetailStatus();
        final Object otherDetailStatus = other.getDetailStatus();
        if (thisDetailStatus == null ? otherDetailStatus != null : !thisDetailStatus.equals(otherDetailStatus)) return false;
        final Object thisSourceHash = this.getSourceHash();
        final Object otherSourceHash = other.getSourceHash();
        if (thisSourceHash == null ? otherSourceHash != null : !thisSourceHash.equals(otherSourceHash)) return false;
        final Object thisSourceFetchedAt = this.getSourceFetchedAt();
        final Object otherSourceFetchedAt = other.getSourceFetchedAt();
        if (thisSourceFetchedAt == null ? otherSourceFetchedAt != null : !thisSourceFetchedAt.equals(otherSourceFetchedAt)) return false;
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
        return other instanceof Person;
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
        final Object hashBangumiPersonId = this.getBangumiPersonId();
        result = result * PRIME + (hashBangumiPersonId == null ? 43 : hashBangumiPersonId.hashCode());
        final Object hashLastSeenImportId = this.getLastSeenImportId();
        result = result * PRIME + (hashLastSeenImportId == null ? 43 : hashLastSeenImportId.hashCode());
        final Object hashSourceActive = this.getSourceActive();
        result = result * PRIME + (hashSourceActive == null ? 43 : hashSourceActive.hashCode());
        final Object hashPersonType = this.getPersonType();
        result = result * PRIME + (hashPersonType == null ? 43 : hashPersonType.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashSummary = this.getSummary();
        result = result * PRIME + (hashSummary == null ? 43 : hashSummary.hashCode());
        final Object hashCareerJson = this.getCareerJson();
        result = result * PRIME + (hashCareerJson == null ? 43 : hashCareerJson.hashCode());
        final Object hashInfoboxJson = this.getInfoboxJson();
        result = result * PRIME + (hashInfoboxJson == null ? 43 : hashInfoboxJson.hashCode());
        final Object hashImage = this.getImage();
        result = result * PRIME + (hashImage == null ? 43 : hashImage.hashCode());
        final Object hashImageSourceUrl = this.getImageSourceUrl();
        result = result * PRIME + (hashImageSourceUrl == null ? 43 : hashImageSourceUrl.hashCode());
        final Object hashImageStorageStatus = this.getImageStorageStatus();
        result = result * PRIME + (hashImageStorageStatus == null ? 43 : hashImageStorageStatus.hashCode());
        final Object hashDetailStatus = this.getDetailStatus();
        result = result * PRIME + (hashDetailStatus == null ? 43 : hashDetailStatus.hashCode());
        final Object hashSourceHash = this.getSourceHash();
        result = result * PRIME + (hashSourceHash == null ? 43 : hashSourceHash.hashCode());
        final Object hashSourceFetchedAt = this.getSourceFetchedAt();
        result = result * PRIME + (hashSourceFetchedAt == null ? 43 : hashSourceFetchedAt.hashCode());
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
        return "Person(id=" + this.getId() + ", bangumiPersonId=" + this.getBangumiPersonId() + ", personType=" + this.getPersonType() + ", name=" + this.getName() + ", summary=" + this.getSummary() + ", careerJson=" + this.getCareerJson() + ", infoboxJson=" + this.getInfoboxJson() + ", image=" + this.getImage() + ", imageSourceUrl=" + this.getImageSourceUrl() + ", imageStorageStatus=" + this.getImageStorageStatus() + ", detailStatus=" + this.getDetailStatus() + ", sourceHash=" + this.getSourceHash() + ", sourceFetchedAt=" + this.getSourceFetchedAt() + ", lastSeenImportId=" + this.getLastSeenImportId() + ", sourceActive=" + this.getSourceActive() + ", createdAt=" + this.getCreatedAt() + ", updatedAt=" + this.getUpdatedAt() + ")";
    }
}
