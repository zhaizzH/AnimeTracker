package top.zhaizz.pojo.dto.evidence;

/**
 * 用于关系扩展的实体类型。PERSON 与 ACTOR 都使用本地 person.id，
 * 但 ACTOR 只沿 character_actor 声优关系扩展。
 */
public enum EvidenceEntityType {
    SUBJECT,
    /** 输入作品 ID，沿 subject_relation 双向扩展关联动画。 */
    RELATION_SUBJECT,
    PERSON,
    CHARACTER,
    ACTOR
}
