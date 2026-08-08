package top.zhaizz.pojo.vo;

import lombok.Data;

/**
 * 标签信息 VO
 */
@Data
public class TagVO {

    private Long id;            // 标签ID
    private String name;        // 标签名
    private Integer count;      // 该标签在此条目上的使用次数
}
