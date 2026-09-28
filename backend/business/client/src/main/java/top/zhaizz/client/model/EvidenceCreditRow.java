package top.zhaizz.client.model;

/**
 * 条目主创人员行（含人物名称）
 */
public class EvidenceCreditRow {
    /**
     * 关联条目标识
     */
    private Long subjectId;
    /**
     * 人物名称
     */
    private String personName;
    /**
     * 人员或角色在关系中的职务
     */
    private String role;
    /**
     * 实体之间的关系类型
     */
    private String relation;

    /** 创建字段均为默认值的空主创行，供结果映射使用 */
    public EvidenceCreditRow() {
    }

    /**
     * 获取关联条目标识
     * @return 主创所属条目的主键，未设置时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取人物名称
     * @return 主创人员姓名，未设置时为 {@code null}
     */
    public String getPersonName() {
        return this.personName;
    }

    /**
     * 获取人员或角色在关系中的职务
     * @return 人员或角色承担的职务，未设置时为 {@code null}
     */
    public String getRole() {
        return this.role;
    }

    /**
     * 获取实体之间的关系类型
     * @return 主创与条目的关系类型，未设置时为 {@code null}
     */
    public String getRelation() {
        return this.relation;
    }

    /**
     * 替换关联条目标识
     * @param subjectId 新的主创所属条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换人物名称
     * @param personName 新的主创人员姓名，可为 {@code null}
     */
    public void setPersonName(final String personName) {
        this.personName = personName;
    }

    /**
     * 替换人员或角色在关系中的职务
     * @param role 新的职务文本，可为 {@code null}
     */
    public void setRole(final String role) {
        this.role = role;
    }

    /**
     * 替换实体之间的关系类型
     * @param relation 新的主创与条目关系类型，可为 {@code null}
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
        if (!(o instanceof EvidenceCreditRow)) return false;
        final EvidenceCreditRow other = (EvidenceCreditRow) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisPersonName = this.getPersonName();
        final Object otherPersonName = other.getPersonName();
        if (thisPersonName == null ? otherPersonName != null : !thisPersonName.equals(otherPersonName)) return false;
        final Object thisRole = this.getRole();
        final Object otherRole = other.getRole();
        if (thisRole == null ? otherRole != null : !thisRole.equals(otherRole)) return false;
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
        return other instanceof EvidenceCreditRow;
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
        final Object hashPersonName = this.getPersonName();
        result = result * PRIME + (hashPersonName == null ? 43 : hashPersonName.hashCode());
        final Object hashRole = this.getRole();
        result = result * PRIME + (hashRole == null ? 43 : hashRole.hashCode());
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
        return "EvidenceCreditRow(subjectId=" + this.getSubjectId() + ", personName=" + this.getPersonName() + ", role=" + this.getRole() + ", relation=" + this.getRelation() + ")";
    }
}
