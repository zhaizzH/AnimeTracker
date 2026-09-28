package top.zhaizz.pojo.vo.subject;

import java.math.BigDecimal;
import java.time.LocalDate;

/** 批量权威回查中可返回的条目字段 */
public class SubjectBatchItemVO {
    /** 记录或资源的唯一标识 */
    private Long id;
    /** 来源数据的原始名称 */
    private String name;
    /** 条目的中文名称 */
    private String nameCn;
    /** 条目的封面图片地址 */
    private String image;
    /** 条目评分，取值遵循接口约定 */
    private BigDecimal score;
    /** 条目评分人数 */
    private Integer ratingTotal;
    /** 条目收藏人数 */
    private Integer collectionTotal;
    /** 条目的首播日期 */
    private LocalDate airDate;
    /** 业务类型或状态编码，取值由所属接口约束 */
    private Integer type;
    /** 条目是否包含 NSFW 内容 */
    private Boolean nsfw;
    /** Agent 权威回查需要的有效状态；由 subject.import_status 派生 */
    private Boolean active;

    /** 创建字段均为默认值的空条目字段 */
    public SubjectBatchItemVO() {
    }

    /**
     * 获取记录或资源的唯一标识
     * @return 条目标识；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取来源数据的原始名称
     * @return 原始名称；未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取条目的中文名称
     * @return 中文名称，可能为空；未提供时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取条目的封面图片地址
     * @return 封面图片地址；未提供时为 {@code null}
     */
    public String getImage() {
        return this.image;
    }

    /**
     * 获取条目评分
     * @return 评分值，取值遵循接口约定；未提供时为 {@code null}
     */
    public BigDecimal getScore() {
        return this.score;
    }

    /**
     * 获取条目评分人数
     * @return 参与评分的人数；未提供时为 {@code null}
     */
    public Integer getRatingTotal() {
        return this.ratingTotal;
    }

    /**
     * 获取条目收藏人数
     * @return 收藏该条目的人数；未提供时为 {@code null}
     */
    public Integer getCollectionTotal() {
        return this.collectionTotal;
    }

    /**
     * 获取条目的首播日期
     * @return 首播日期；未提供时为 {@code null}
     */
    public LocalDate getAirDate() {
        return this.airDate;
    }

    /**
     * 获取业务类型或状态编码
     * @return 类型或状态编码，取值由所属接口约束；未提供时为 {@code null}
     */
    public Integer getType() {
        return this.type;
    }

    /**
     * 获取条目是否包含 NSFW 内容
     * @return 包含 NSFW 内容时为 {@code true}；未提供时为 {@code null}
     */
    public Boolean getNsfw() {
        return this.nsfw;
    }

    /**
     * 获取 Agent 权威回查需要的有效状态
     * @return 由 {@code subject.import_status} 派生的有效状态；未提供时为 {@code null}
     */
    public Boolean getActive() {
        return this.active;
    }

    /**
     * 替换记录或资源的唯一标识
     * @param id 条目标识，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换来源数据的原始名称
     * @param name 原始名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换条目的中文名称
     * @param nameCn 中文名称，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换条目的封面图片地址
     * @param image 封面图片地址，可为 {@code null}
     */
    public void setImage(final String image) {
        this.image = image;
    }

    /**
     * 替换条目评分
     * @param score 评分值，可为 {@code null}，具体取值遵循接口约定
     */
    public void setScore(final BigDecimal score) {
        this.score = score;
    }

    /**
     * 替换条目评分人数
     * @param ratingTotal 参与评分的人数，可为 {@code null}
     */
    public void setRatingTotal(final Integer ratingTotal) {
        this.ratingTotal = ratingTotal;
    }

    /**
     * 替换条目收藏人数
     * @param collectionTotal 收藏该条目的人数，可为 {@code null}
     */
    public void setCollectionTotal(final Integer collectionTotal) {
        this.collectionTotal = collectionTotal;
    }

    /**
     * 替换条目的首播日期
     * @param airDate 首播日期，可为 {@code null}
     */
    public void setAirDate(final LocalDate airDate) {
        this.airDate = airDate;
    }

    /**
     * 替换业务类型或状态编码
     * @param type 类型或状态编码，可为 {@code null}，取值由所属接口约束
     */
    public void setType(final Integer type) {
        this.type = type;
    }

    /**
     * 替换条目是否包含 NSFW 内容的标记
     * @param nsfw 包含 NSFW 内容时为 {@code true}，可为 {@code null}
     */
    public void setNsfw(final Boolean nsfw) {
        this.nsfw = nsfw;
    }

    /**
     * 替换 Agent 权威回查需要的有效状态
     * @param active 由 {@code subject.import_status} 派生的有效状态，可为 {@code null}
     */
    public void setActive(final Boolean active) {
        this.active = active;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectBatchItemVO)) return false;
        final SubjectBatchItemVO other = (SubjectBatchItemVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisRatingTotal = this.getRatingTotal();
        final Object otherRatingTotal = other.getRatingTotal();
        if (thisRatingTotal == null ? otherRatingTotal != null : !thisRatingTotal.equals(otherRatingTotal)) return false;
        final Object thisCollectionTotal = this.getCollectionTotal();
        final Object otherCollectionTotal = other.getCollectionTotal();
        if (thisCollectionTotal == null ? otherCollectionTotal != null : !thisCollectionTotal.equals(otherCollectionTotal)) return false;
        final Object thisType = this.getType();
        final Object otherType = other.getType();
        if (thisType == null ? otherType != null : !thisType.equals(otherType)) return false;
        final Object thisNsfw = this.getNsfw();
        final Object otherNsfw = other.getNsfw();
        if (thisNsfw == null ? otherNsfw != null : !thisNsfw.equals(otherNsfw)) return false;
        final Object thisActive = this.getActive();
        final Object otherActive = other.getActive();
        if (thisActive == null ? otherActive != null : !thisActive.equals(otherActive)) return false;
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
        return other instanceof SubjectBatchItemVO;
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
        final Object hashRatingTotal = this.getRatingTotal();
        result = result * PRIME + (hashRatingTotal == null ? 43 : hashRatingTotal.hashCode());
        final Object hashCollectionTotal = this.getCollectionTotal();
        result = result * PRIME + (hashCollectionTotal == null ? 43 : hashCollectionTotal.hashCode());
        final Object hashType = this.getType();
        result = result * PRIME + (hashType == null ? 43 : hashType.hashCode());
        final Object hashNsfw = this.getNsfw();
        result = result * PRIME + (hashNsfw == null ? 43 : hashNsfw.hashCode());
        final Object hashActive = this.getActive();
        result = result * PRIME + (hashActive == null ? 43 : hashActive.hashCode());
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
        return "SubjectBatchItemVO(id=" + this.getId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", image=" + this.getImage() + ", score=" + this.getScore() + ", ratingTotal=" + this.getRatingTotal() + ", collectionTotal=" + this.getCollectionTotal() + ", airDate=" + this.getAirDate() + ", type=" + this.getType() + ", nsfw=" + this.getNsfw() + ", active=" + this.getActive() + ")";
    }
}
