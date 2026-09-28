package top.zhaizz.pojo.vo.subject;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 剧集信息 VO
 */
public class EpisodeVO {

    /** 剧集ID */
    private Long id;            // 剧集ID
    /** 所属条目ID */
    private Long subjectId;     // 所属条目ID
    /** 剧集类型: 0=本篇, 1=SP, 2=OP, 3=ED, 4=预告 */
    private Integer type;       // 剧集类型: 0=本篇, 1=SP, 2=OP, 3=ED, 4=预告
    /** 集数序号（支持小数点） */
    private BigDecimal sort;    // 集数序号（支持小数点）
    /** 日文/英文标题 */
    private String name;        // 日文/英文标题
    /** 中文标题 */
    private String nameCn;      // 中文标题
    /** 时长（如 "24m"） */
    private String duration;    // 时长（如 "24m"）
    /** 播出日期 */
    private LocalDate airdate;  // 播出日期
    /** 剧情简介 */
    private String description; // 剧情简介
    /** 播出状态: Air=已播出, Today=今日播出, NA=未播出 */
    private String status;      // 播出状态: Air=已播出, Today=今日播出, NA=未播出

    /** 创建字段均为默认值的空剧集信息 */
    public EpisodeVO() {
    }

    /**
     * 获取剧集ID
     * @return 剧集主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取所属条目ID
     * @return 所属条目主键，用于将剧集归属到条目；未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取剧集类型
     * @return 剧集类型编码；0=本篇, 1=SP, 2=OP, 3=ED, 4=预告，未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取集数序号
     * @return 支持小数点的集数序号（如 1.5）；未提供时为 {@code null}
     */
    public BigDecimal getSort() {
        return this.sort;
    }

    /**
     * 获取日文/英文标题
     * @return 原始语言标题；未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取中文标题
     * @return 中文标题，可能为空；未提供时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取时长
     * @return 形如 {@code "24m"} 的时长文本；未提供时为 {@code null}
     */
    public String getDuration() {
        return this.duration;
    }

    /**
     * 获取播出日期
     * @return 该集的播出日期；未提供时为 {@code null}
     */
    public LocalDate getAirdate() {
        return this.airdate;
    }

    /**
     * 获取剧情简介
     * @return 该集剧情简介；未提供时为 {@code null}
     */
    public String getDescription() {
        return this.description;
    }

    /**
     * 获取播出状态
     * @return 播出状态文本；Air=已播出, Today=今日播出, NA=未播出，未提供时为 {@code null}
     */
    public String getStatus() {
        return this.status;
    }

    /**
     * 替换剧集ID
     * @param id 剧集主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换所属条目ID
     * @param subjectId 所属条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换剧集类型
     * @param type 剧集类型编码；0=本篇, 1=SP, 2=OP, 3=ED, 4=预告，可为 {@code null}
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换集数序号
     * @param sort 支持小数点的集数序号，可为 {@code null}
     */
    public void setSort(final BigDecimal sort) {
        this.sort = sort;
    }

    /**
     * 替换日文/英文标题
     * @param name 原始语言标题，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换中文标题
     * @param nameCn 中文标题，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换时长
     * @param duration 形如 {@code "24m"} 的时长文本，可为 {@code null}
     */
    public void setDuration(final String duration) {
        this.duration = duration;
    }

    /**
     * 替换播出日期
     * @param airdate 该集的播出日期，可为 {@code null}
     */
    public void setAirdate(final LocalDate airdate) {
        this.airdate = airdate;
    }

    /**
     * 替换剧情简介
     * @param description 该集剧情简介，可为 {@code null}
     */
    public void setDescription(final String description) {
        this.description = description;
    }

    /**
     * 替换播出状态
     * @param status 播出状态文本；Air=已播出, Today=今日播出, NA=未播出，可为 {@code null}
     */
    public void setStatus(final String status) {
        this.status = status;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof EpisodeVO)) return false;
        final EpisodeVO other = (EpisodeVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisSort = this.getSort();
        final Object otherSort = other.getSort();
        if (thisSort == null ? otherSort != null : !thisSort.equals(otherSort)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisNameCn = this.getNameCn();
        final Object otherNameCn = other.getNameCn();
        if (thisNameCn == null ? otherNameCn != null : !thisNameCn.equals(otherNameCn)) return false;
        final Object thisDuration = this.getDuration();
        final Object otherDuration = other.getDuration();
        if (thisDuration == null ? otherDuration != null : !thisDuration.equals(otherDuration)) return false;
        final Object thisAirdate = this.getAirdate();
        final Object otherAirdate = other.getAirdate();
        if (thisAirdate == null ? otherAirdate != null : !thisAirdate.equals(otherAirdate)) return false;
        final Object thisDescription = this.getDescription();
        final Object otherDescription = other.getDescription();
        if (thisDescription == null ? otherDescription != null : !thisDescription.equals(otherDescription)) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof EpisodeVO;
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
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashSort = this.getSort();
        result = result * PRIME + (hashSort == null ? 43 : hashSort.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashNameCn = this.getNameCn();
        result = result * PRIME + (hashNameCn == null ? 43 : hashNameCn.hashCode());
        final Object hashDuration = this.getDuration();
        result = result * PRIME + (hashDuration == null ? 43 : hashDuration.hashCode());
        final Object hashAirdate = this.getAirdate();
        result = result * PRIME + (hashAirdate == null ? 43 : hashAirdate.hashCode());
        final Object hashDescription = this.getDescription();
        result = result * PRIME + (hashDescription == null ? 43 : hashDescription.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "EpisodeVO(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", type=" + this.getType() + ", sort=" + this.getSort() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", duration=" + this.getDuration() + ", airdate=" + this.getAirdate() + ", description=" + this.getDescription() + ", status=" + this.getStatus() + ")";
    }
}
