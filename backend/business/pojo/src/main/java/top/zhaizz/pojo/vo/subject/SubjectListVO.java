package top.zhaizz.pojo.vo.subject;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 条目列表视图（摘要信息）
 */
public class SubjectListVO {

    /** 条目ID */
    private Long id;            // 条目ID
    /** 日文/英文名 */
    private String name;        // 日文/英文名
    /** 中文名 */
    private String nameCn;      // 中文名
    /** 封面图URL */
    private String image;       // 封面图URL
    /** Bangumi 评分（0.0~10.0） */
    private BigDecimal score;   // Bangumi 评分（0.0~10.0）
    /** Bangumi 排名 */
    private Integer rank;       // Bangumi 排名
    /** 总集数 */
    private Integer eps;        // 总集数
    /** 播出日期 */
    private LocalDate airDate;  // 播出日期
    /** 条目类型（2=动画） */
    private Integer type;       // 条目类型（2=动画）
    /** 播出星期（0=周日, 1=周一 ... 6=周六） */
    private Integer airWeekday; // 播出星期（0=周日, 1=周一 ... 6=周六）
    /** 收藏数 */
    private Integer collectionTotal;    // 收藏数

    /** 创建字段均为默认值的空条目摘要 */
    public SubjectListVO() {
    }

    /**
     * 获取条目ID
     * @return 条目主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取日文/英文名
     * @return 原始语言名称；未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取中文名
     * @return 中文名称，可能为空；未提供时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取封面图URL
     * @return 封面图地址；未提供时为 {@code null}
     */
    public String getImage() {
        return this.image;
    }

    /**
     * 获取 Bangumi 评分
     * @return 取值范围 0.0~10.0 的评分；未提供时为 {@code null}
     */
    public BigDecimal getScore() {
        return this.score;
    }

    /**
     * 获取 Bangumi 排名
     * @return 排名名次；未提供时为 {@code null}
     */
    public Integer getRank() {
        return this.rank;
    }

    /**
     * 获取总集数
     * @return 条目总集数；未提供时为 {@code null}
     */
    public Integer getEps() {
        return this.eps;
    }

    /**
     * 获取播出日期
     * @return 首播日期；未提供时为 {@code null}
     */
    public LocalDate getAirDate() {
        return this.airDate;
    }

    /**
     * 获取条目类型
     * @return 条目类型编码；2 表示动画，未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
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
     * 替换条目ID
     * @param id 条目主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换日文/英文名
     * @param name 原始语言名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换中文名
     * @param nameCn 中文名称，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换封面图URL
     * @param image 封面图地址，可为 {@code null}
     */
    public void setImage(final String image) {
        this.image = image;
    }

    /**
     * 替换 Bangumi 评分
     * @param score 取值范围 0.0~10.0 的评分，可为 {@code null}
     */
    public void setScore(final BigDecimal score) {
        this.score = score;
    }

    /**
     * 替换 Bangumi 排名
     * @param rank 排名名次，可为 {@code null}
     */
    public void setRank(final Integer rank) {
        this.rank = rank;
    }

    /**
     * 替换总集数
     * @param eps 条目总集数，可为 {@code null}
     */
    public void setEps(final Integer eps) {
        this.eps = eps;
    }

    /**
     * 替换播出日期
     * @param airDate 首播日期，可为 {@code null}
     */
    public void setAirDate(final LocalDate airDate) {
        this.airDate = airDate;
    }

    /**
     * 替换条目类型
     * @param type 条目类型编码，可为 {@code null}；2 表示动画
     */
    public void setType(final Integer type) {
        this.type = type;
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
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectListVO)) return false;
        final SubjectListVO other = (SubjectListVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisRank = this.getRank();
        final Object otherRank = other.getRank();
        if (thisRank == null ? otherRank != null : !thisRank.equals(otherRank)) return false;
        final Object thisEps = this.getEps();
        final Object otherEps = other.getEps();
        if (thisEps == null ? otherEps != null : !thisEps.equals(otherEps)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisAirWeekday = this.getAirWeekday();
        final Object otherAirWeekday = other.getAirWeekday();
        if (thisAirWeekday == null ? otherAirWeekday != null : !thisAirWeekday.equals(otherAirWeekday)) return false;
        final Object thisCollectionTotal = this.getCollectionTotal();
        final Object otherCollectionTotal = other.getCollectionTotal();
        if (thisCollectionTotal == null ? otherCollectionTotal != null : !thisCollectionTotal.equals(otherCollectionTotal)) return false;
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
        return other instanceof SubjectListVO;
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
        final Object hashRank = this.getRank();
        result = result * PRIME + (hashRank == null ? 43 : hashRank.hashCode());
        final Object hashEps = this.getEps();
        result = result * PRIME + (hashEps == null ? 43 : hashEps.hashCode());
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashAirWeekday = this.getAirWeekday();
        result = result * PRIME + (hashAirWeekday == null ? 43 : hashAirWeekday.hashCode());
        final Object hashCollectionTotal = this.getCollectionTotal();
        result = result * PRIME + (hashCollectionTotal == null ? 43 : hashCollectionTotal.hashCode());
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
        return "SubjectListVO(id=" + this.getId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", image=" + this.getImage() + ", score=" + this.getScore() + ", rank=" + this.getRank() + ", eps=" + this.getEps() + ", airDate=" + this.getAirDate() + ", type=" + this.getType() + ", airWeekday=" + this.getAirWeekday() + ", collectionTotal=" + this.getCollectionTotal() + ")";
    }
}
