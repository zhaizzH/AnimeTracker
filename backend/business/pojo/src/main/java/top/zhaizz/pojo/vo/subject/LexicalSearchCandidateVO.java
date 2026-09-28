package top.zhaizz.pojo.vo.subject;

import java.math.BigDecimal;

/** MySQL FULLTEXT 召回候选；详细事实仍需通过 Evidence API 回查 */
public class LexicalSearchCandidateVO {
    /** 关联条目标识 */
    private Long subjectId;
    /** 来源数据的原始名称 */
    private String name;
    /** 条目的中文名称 */
    private String nameCn;
    /** 词法检索相关性得分 */
    private BigDecimal lexicalScore;
    /** 候选结果排序名次 */
    private Integer rank;

    /** 创建字段均为默认值的空召回候选 */
    public LexicalSearchCandidateVO() {
    }

    /**
     * 创建携带全部字段的召回候选
     * @param subjectId 关联条目标识，可为 {@code null}
     * @param name 来源数据的原始名称，可为 {@code null}
     * @param nameCn 条目的中文名称，可为 {@code null}
     * @param lexicalScore 词法检索相关性得分，可为 {@code null}
     * @param rank 候选结果排序名次，可为 {@code null}
     */
    public LexicalSearchCandidateVO(final Long subjectId, final String name, final String nameCn, final BigDecimal lexicalScore, final Integer rank) {
        this.subjectId = subjectId;
        this.name = name;
        this.nameCn = nameCn;
        this.lexicalScore = lexicalScore;
        this.rank = rank;
    }

    /**
     * 创建构建器，用于链式组装召回候选
     * @return 空的召回候选构建器
     */
    public static LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder builder() {
        return new LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder();
    }

    /**
     * 获取关联条目标识
     * @return 条目标识；未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
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
     * 获取词法检索相关性得分
     * @return 相关性得分，通常越大越相关；未提供时为 {@code null}
     */
    public BigDecimal getLexicalScore() {
        return this.lexicalScore;
    }

    /**
     * 获取候选结果排序名次
     * @return 名次，通常从 1 开始；未提供时为 {@code null}
     */
    public Integer getRank() {
        return this.rank;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 条目标识，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
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
     * 替换词法检索相关性得分
     * @param lexicalScore 相关性得分，可为 {@code null}
     */
    public void setLexicalScore(final BigDecimal lexicalScore) {
        this.lexicalScore = lexicalScore;
    }

    /**
     * 替换候选结果排序名次
     * @param rank 名次，可为 {@code null}
     */
    public void setRank(final Integer rank) {
        this.rank = rank;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LexicalSearchCandidateVO)) return false;
        final LexicalSearchCandidateVO other = (LexicalSearchCandidateVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisRank = this.getRank();
        final Object otherRank = other.getRank();
        if (thisRank == null ? otherRank != null : !thisRank.equals(otherRank)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisNameCn = this.getNameCn();
        final Object otherNameCn = other.getNameCn();
        if (thisNameCn == null ? otherNameCn != null : !thisNameCn.equals(otherNameCn)) return false;
        final Object thisLexicalScore = this.getLexicalScore();
        final Object otherLexicalScore = other.getLexicalScore();
        if (thisLexicalScore == null ? otherLexicalScore != null : !thisLexicalScore.equals(otherLexicalScore)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof LexicalSearchCandidateVO;
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
        final Object hashRank = this.getRank();
        result = result * PRIME + (hashRank == null ? 43 : hashRank.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashNameCn = this.getNameCn();
        result = result * PRIME + (hashNameCn == null ? 43 : hashNameCn.hashCode());
        final Object hashLexicalScore = this.getLexicalScore();
        result = result * PRIME + (hashLexicalScore == null ? 43 : hashLexicalScore.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "LexicalSearchCandidateVO(subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", lexicalScore=" + this.getLexicalScore() + ", rank=" + this.getRank() + ")";
    }

    /**
     * {@code LexicalSearchCandidateVO} 的链式构建器
     *
     * <p>各字段默认均为 {@code null}，未显式设置时构建结果对应字段保持 {@code null}
     */
    public static class LexicalSearchCandidateVOBuilder {
        /** 关联条目标识 */
        private Long subjectId;
        /** 来源数据的原始名称 */
        private String name;
        /** 条目的中文名称 */
        private String nameCn;
        /** 词法检索相关性得分 */
        private BigDecimal lexicalScore;
        /** 候选结果排序名次 */
        private Integer rank;

        /** 创建字段均为未设置状态的空构建器 */
        LexicalSearchCandidateVOBuilder() {
        }

        /**
         * 设置关联条目标识，覆盖此前取值
         * @param subjectId 条目标识，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder subjectId(final Long subjectId) {
            this.subjectId = subjectId;
            return this;
        }

        /**
         * 设置来源数据的原始名称，覆盖此前取值
         * @param name 原始名称，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder name(final String name) {
            this.name = name;
            return this;
        }

        /**
         * 设置条目的中文名称，覆盖此前取值
         * @param nameCn 中文名称，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder nameCn(final String nameCn) {
            this.nameCn = nameCn;
            return this;
        }

        /**
         * 设置词法检索相关性得分，覆盖此前取值
         * @param lexicalScore 相关性得分，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder lexicalScore(final BigDecimal lexicalScore) {
            this.lexicalScore = lexicalScore;
            return this;
        }

        /**
         * 设置候选结果排序名次，覆盖此前取值
         * @param rank 名次，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder rank(final Integer rank) {
            this.rank = rank;
            return this;
        }

        /**
         * 构建召回候选，各字段取构建器当前取值
         * @return 携带当前构建器取值的召回候选
         */
        public LexicalSearchCandidateVO build() {
            return new LexicalSearchCandidateVO(this.subjectId, this.name, this.nameCn, this.lexicalScore, this.rank);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "LexicalSearchCandidateVO.LexicalSearchCandidateVOBuilder(subjectId=" + this.subjectId + ", name=" + this.name + ", nameCn=" + this.nameCn + ", lexicalScore=" + this.lexicalScore + ", rank=" + this.rank + ")";
        }
    }
}
