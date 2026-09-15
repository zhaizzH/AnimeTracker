package top.zhaizz.pojo.dto.evidence;

/**
 * 用于关系扩展的实体类型。PERSON 与 ACTOR 都使用本地 person.id，
 * 但 ACTOR 只沿 character_actor 声优关系扩展
 */
public enum EvidenceEntityType {
    /**
     * 直接回查本地条目
     */
    SUBJECT,
    /** 输入作品 ID，沿 subject_relation 双向扩展关联动画 */
    RELATION_SUBJECT,
    /**
     * 按本地人物主创关系扩展动画条目
     */
    PERSON,
    /**
     * 按本地角色关系扩展动画条目
     */
    CHARACTER,
    /**
     * 按本地人物的声优关系扩展动画条目
     */
    ACTOR
}
