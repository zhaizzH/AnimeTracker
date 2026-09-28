package top.zhaizz.client.model;

import java.math.BigDecimal;

/**
 * search_document 的受控词法召回行
 */
public class LexicalSearchRow {
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
     * 词法检索相关性得分
     */
    private BigDecimal lexicalScore;

    /** 创建字段均为默认值的空召回行，供结果映射使用 */
    public LexicalSearchRow() {
    }

    /**
     * 获取关联条目标识
     * @return 召回条目主键，未设置时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取来源数据的原始名称
     * @return 召回条目的原始语言名称，未设置时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取条目的中文名称
     * @return 召回条目的中文名称，未设置时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取词法检索相关性得分
     * @return 词法匹配得分，未设置时为 {@code null}
     */
    public BigDecimal getLexicalScore() {
        return this.lexicalScore;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 新的召回条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换来源数据的原始名称
     * @param name 新的召回条目原始语言名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换条目的中文名称
     * @param nameCn 新的召回条目中文名称，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换词法检索相关性得分
     * @param lexicalScore 新的词法匹配得分，可为 {@code null}
     */
    public void setLexicalScore(final BigDecimal lexicalScore) {
        this.lexicalScore = lexicalScore;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LexicalSearchRow)) return false;
        final LexicalSearchRow other = (LexicalSearchRow) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
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
        return other instanceof LexicalSearchRow;
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
        return "LexicalSearchRow(subjectId=" + this.getSubjectId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", lexicalScore=" + this.getLexicalScore() + ")";
    }
}
