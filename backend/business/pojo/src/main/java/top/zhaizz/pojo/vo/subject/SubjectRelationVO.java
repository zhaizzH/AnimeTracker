package top.zhaizz.pojo.vo.subject;

/**
 * 条目关联视图
 */
public class SubjectRelationVO {

    /** 关联类型: prequel, sequel, side_story 等 */
    private String relation;            // 关联类型: prequel, sequel, side_story 等
    /** 关联条目信息 */
    private SubjectListVO relatedSubject;   // 关联条目信息

    /** 创建字段均为默认值的空关联视图 */
    public SubjectRelationVO() {
    }

    /**
     * 创建携带全部字段的关联视图
     * @param relation 关联类型，可为 {@code null}
     * @param relatedSubject 关联条目信息，可为 {@code null}
     */
    public SubjectRelationVO(final String relation, final SubjectListVO relatedSubject) {
        this.relation = relation;
        this.relatedSubject = relatedSubject;
    }

    /**
     * 获取关联类型
     * @return 形如 prequel、sequel、side_story 的关联类型；未提供时为 {@code null}
     */
    public String getRelation() {
        return this.relation;
    }

    /**
     * 获取关联条目信息
     * @return 被关联条目的摘要信息；未提供时为 {@code null}
     */
    public SubjectListVO getRelatedSubject() {
        return this.relatedSubject;
    }

    /**
     * 替换关联类型
     * @param relation 形如 prequel、sequel、side_story 的关联类型，可为 {@code null}
     */
    public void setRelation(final String relation) {
        this.relation = relation;
    }

    /**
     * 替换关联条目信息
     * @param relatedSubject 被关联条目的摘要信息，可为 {@code null}
     */
    public void setRelatedSubject(final SubjectListVO relatedSubject) {
        this.relatedSubject = relatedSubject;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectRelationVO)) return false;
        final SubjectRelationVO other = (SubjectRelationVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisRelation = this.getRelation();
        final Object otherRelation = other.getRelation();
        if (thisRelation == null ? otherRelation != null : !thisRelation.equals(otherRelation)) return false;
        final Object thisRelatedSubject = this.getRelatedSubject();
        final Object otherRelatedSubject = other.getRelatedSubject();
        if (thisRelatedSubject == null ? otherRelatedSubject != null : !thisRelatedSubject.equals(otherRelatedSubject)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectRelationVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashRelation = this.getRelation();
        result = result * PRIME + (hashRelation == null ? 43 : hashRelation.hashCode());
        final Object hashRelatedSubject = this.getRelatedSubject();
        result = result * PRIME + (hashRelatedSubject == null ? 43 : hashRelatedSubject.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectRelationVO(relation=" + this.getRelation() + ", relatedSubject=" + this.getRelatedSubject() + ")";
    }
}
