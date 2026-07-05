package top.zhaizz.animetracker.subject.vo;

import lombok.Data;

/**
 * 标签信息 VO
 */
@Data
public class TagVO {

    private Long id;
    private String name;
    private Integer count;
}
