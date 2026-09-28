package top.zhaizz.pojo.vo.collection;

import top.zhaizz.pojo.vo.subject.SubjectListVO;

/**
 * 用户收藏视图
 */
public class UserCollectionVO {

    /** 收藏ID */
    private Long id; // 收藏ID
    /** 条目ID */
    private Long subjectId; // 条目ID
    /** 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃 */
    private Integer type; // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    /** 评分（0~10, 0 表示未评分） */
    private Integer rate; // 评分（0~10, 0 表示未评分）
    /** 看到第几集 */
    private Integer epStatus; // 看到第几集
    /** 条目信息 */
    private SubjectListVO subject; // 条目信息

    /** 创建字段均为默认值的空收藏视图 */
    public UserCollectionVO() {
    }

    /**
     * 获取收藏ID
     * @return 用户收藏记录主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
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
     * 获取条目信息
     * @return 收藏对应的条目详情；未提供时为 {@code null}
     */
    public SubjectListVO getSubject() {
        return this.subject;
    }

    /**
     * 替换收藏ID
     * @param id 用户收藏记录主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
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
     * 替换条目信息
     * @param subject 收藏对应的条目详情，可为 {@code null}
     */
    public void setSubject(final SubjectListVO subject) {
        this.subject = subject;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof UserCollectionVO)) return false;
        final UserCollectionVO other = (UserCollectionVO) o;
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
        final Object thisRate = this.getRate();
        final Object otherRate = other.getRate();
        if (thisRate == null ? otherRate != null : !thisRate.equals(otherRate)) return false;
        final Object thisEpStatus = this.getEpStatus();
        final Object otherEpStatus = other.getEpStatus();
        if (thisEpStatus == null ? otherEpStatus != null : !thisEpStatus.equals(otherEpStatus)) return false;
        final Object thisSubject = this.getSubject();
        final Object otherSubject = other.getSubject();
        if (thisSubject == null ? otherSubject != null : !thisSubject.equals(otherSubject)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof UserCollectionVO;
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
        final Object hashRate = this.getRate();
        result = result * PRIME + (hashRate == null ? 43 : hashRate.hashCode());
        final Object hashEpStatus = this.getEpStatus();
        result = result * PRIME + (hashEpStatus == null ? 43 : hashEpStatus.hashCode());
        final Object hashSubject = this.getSubject();
        result = result * PRIME + (hashSubject == null ? 43 : hashSubject.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "UserCollectionVO(id=" + this.getId() + ", subjectId=" + this.getSubjectId() + ", type=" + this.getType() + ", rate=" + this.getRate() + ", epStatus=" + this.getEpStatus() + ", subject=" + this.getSubject() + ")";
    }
}
