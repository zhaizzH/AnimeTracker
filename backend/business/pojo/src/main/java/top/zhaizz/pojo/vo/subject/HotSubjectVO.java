package top.zhaizz.pojo.vo.subject;

import lombok.Data;

/**
 * 热门榜条目
 */
@Data
public class HotSubjectVO {
    /** 条目ID */
    private Long id;                // 条目ID
    /** 日文/英文名 */
    private String name;            // 日文/英文名
    /** 中文名 */
    private String nameCn;          // 中文名
    /** 封面图URL */
    private String image;           // 封面图URL
    /** 收藏数 */
    private long collectionCount;   // 收藏数
}
