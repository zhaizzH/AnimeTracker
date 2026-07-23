package top.zhaizz.pojo.vo;

import lombok.Data;

/**
 * 用户收藏视图
 */
@Data
public class UserCollectionVO {

    private Long id;
    private Long subjectId;
    private Integer type;       // 收藏类型: 1=想看 2=看过 3=在看 4=搁置 5=抛弃
    private Integer rate;
    private Integer epStatus;  // 剧集进度
    private SubjectListVO subject;
}
