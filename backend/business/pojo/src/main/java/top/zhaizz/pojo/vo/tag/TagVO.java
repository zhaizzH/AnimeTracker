package top.zhaizz.pojo.vo.tag;

import lombok.Data;

/**
 * 标签信息 VO。
 */
@Data
public class TagVO {

    /** 标签ID。 */
    private Long id;            // 标签ID
    /** 标签名。 */
    private String name;        // 标签名
    /** 该标签在此条目上的使用次数。 */
    private Integer count;      // 该标签在此条目上的使用次数
}
