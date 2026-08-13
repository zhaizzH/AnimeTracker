package top.zhaizz.pojo.vo.subject;

import lombok.Data;

/**
 * 热门榜条目
 */
@Data
public class HotSubjectVO {
    private Long id;                // 条目ID
    private String name;            // 日文/英文名
    private String nameCn;          // 中文名
    private String image;           // 封面图URL
    private long collectionCount;   // 收藏数
}
