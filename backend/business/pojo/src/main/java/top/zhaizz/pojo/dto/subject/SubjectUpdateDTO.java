package top.zhaizz.pojo.dto.subject;

import java.time.LocalDate;

/**
 * 编辑条目请求 DTO（所有字段可选）
 */
public class SubjectUpdateDTO {
    /**
     * 日文/英文名
     */
    private String name; // 日文/英文名
    /**
     * 中文名
     */
    private String nameCn; // 中文名
    /**
     * 简介/描述
     */
    private String summary; // 简介/描述
    /**
     * 条目类型（2=动画）
     */
    private Integer type; // 条目类型（2=动画）
    /**
     * 总集数
     */
    private Integer eps; // 总集数
    /**
     * 播出日期
     */
    private LocalDate airDate; // 播出日期
    /**
     * 封面图URL
     */
    private String image; // 封面图URL

    /** 创建全部字段留空的部分更新请求对象 */
    public SubjectUpdateDTO() {
    }

    /**
     * 获取条目名称
     * @return 日文或英文原名；为 {@code null} 时表示不更新名称
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取中文名
     * @return 条目的中文名；为 {@code null} 时表示不更新中文名
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取简介
     * @return 条目的简介或描述文本；为 {@code null} 时表示不更新简介
     */
    public String getSummary() {
        return this.summary;
    }

    /**
     * 获取条目类型
     * @return 条目类型，2=动画；为 {@code null} 时表示不更新类型
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取总集数
     * @return 条目总集数；为 {@code null} 时表示不更新集数
     */
    public Integer getEps() {
        return this.eps;
    }

    /**
     * 获取播出日期
     * @return 条目首播日期；为 {@code null} 时表示不更新播出日期
     */
    public LocalDate getAirDate() {
        return this.airDate;
    }

    /**
     * 获取封面图URL
     * @return 条目封面图地址；为 {@code null} 时表示不更新封面图
     */
    public String getImage() {
        return this.image;
    }

    /**
     * 替换条目名称
     * @param name 日文或英文原名；可为 {@code null} 表示不更新名称
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换中文名
     * @param nameCn 条目的中文名；可为 {@code null} 表示不更新中文名
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换简介
     * @param summary 条目的简介或描述文本；可为 {@code null} 表示不更新简介
     */
    public void setSummary(final String summary) {
        this.summary = summary;
    }

    /**
     * 替换条目类型
     * @param type 条目类型，2=动画；可为 {@code null} 表示不更新类型
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换总集数
     * @param eps 条目总集数；可为 {@code null} 表示不更新集数
     */
    public void setEps(final Integer eps) {
        this.eps = eps;
    }

    /**
     * 替换播出日期
     * @param airDate 条目首播日期；可为 {@code null} 表示不更新播出日期
     */
    public void setAirDate(final LocalDate airDate) {
        this.airDate = airDate;
    }

    /**
     * 替换封面图URL
     * @param image 条目封面图地址；可为 {@code null} 表示不更新封面图
     */
    public void setImage(final String image) {
        this.image = image;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectUpdateDTO)) return false;
        final SubjectUpdateDTO other = (SubjectUpdateDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisEps = this.getEps();
        final Object otherEps = other.getEps();
        if (thisEps == null ? otherEps != null : !thisEps.equals(otherEps)) return false;
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
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectUpdateDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashEps = this.getEps();
        result = result * PRIME + (hashEps == null ? 43 : hashEps.hashCode());
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
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectUpdateDTO(name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", summary=" + this.getSummary() + ", type=" + this.getType() + ", eps=" + this.getEps() + ", airDate=" + this.getAirDate() + ", image=" + this.getImage() + ")";
    }
}
