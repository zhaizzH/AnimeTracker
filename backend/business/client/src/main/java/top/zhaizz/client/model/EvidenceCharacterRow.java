package top.zhaizz.client.model;

/**
 * 条目角色行（含角色名称）
 */
public class EvidenceCharacterRow {
    /**
     * 关联条目标识
     */
    private Long subjectId;
    /**
     * 角色名称
     */
    private String characterName;
    /**
     * 实体之间的关系类型
     */
    private String relation;

    /** 创建字段均为默认值的空角色行，供结果映射使用 */
    public EvidenceCharacterRow() {
    }

    /**
     * 获取关联条目标识
     * @return 角色所属条目的主键，未设置时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取角色名称
     * @return 角色名文本，未设置时为 {@code null}
     */
    public String getCharacterName() {
        return this.characterName;
    }

    /**
     * 获取实体之间的关系类型
     * @return 角色与条目的关系类型，未设置时为 {@code null}
     */
    public String getRelation() {
        return this.relation;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 新的角色所属条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换角色名称
     * @param characterName 新的角色名文本，可为 {@code null}
     */
    public void setCharacterName(final String characterName) {
        this.characterName = characterName;
    }

    /**
     * 替换实体之间的关系类型
     * @param relation 新的角色与条目关系类型，可为 {@code null}
     */
    public void setRelation(final String relation) {
        this.relation = relation;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof EvidenceCharacterRow)) return false;
        final EvidenceCharacterRow other = (EvidenceCharacterRow) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisCharacterName = this.getCharacterName();
        final Object otherCharacterName = other.getCharacterName();
        if (thisCharacterName == null ? otherCharacterName != null : !thisCharacterName.equals(otherCharacterName)) return false;
        final Object thisRelation = this.getRelation();
        final Object otherRelation = other.getRelation();
        if (thisRelation == null ? otherRelation != null : !thisRelation.equals(otherRelation)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof EvidenceCharacterRow;
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
        final Object hashCharacterName = this.getCharacterName();
        result = result * PRIME + (hashCharacterName == null ? 43 : hashCharacterName.hashCode());
        final Object hashRelation = this.getRelation();
        result = result * PRIME + (hashRelation == null ? 43 : hashRelation.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "EvidenceCharacterRow(subjectId=" + this.getSubjectId() + ", characterName=" + this.getCharacterName() + ", relation=" + this.getRelation() + ")";
    }
}
