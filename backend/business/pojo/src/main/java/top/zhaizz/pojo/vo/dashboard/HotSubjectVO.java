package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 热门榜条目
 */
@Data
public class HotSubjectVO {
    private Long id;
    private String name;
    private String nameCn;
    private String image;
    private long collectionCount;
}
