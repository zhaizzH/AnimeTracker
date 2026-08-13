package top.zhaizz.pojo.vo.collection;

import lombok.Data;
import top.zhaizz.pojo.vo.subject.SubjectListVO;

/**
 * 用户收藏视图
 */
@Data
public class UserCollectionVO {

    private Long id;            // 收藏ID
    private Long subjectId;     // 条目ID
    private Integer type;       // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃
    private Integer rate;       // 评分（0~10, 0 表示未评分）
    private Integer epStatus;   // 看到第几集
    private SubjectListVO subject;  // 条目信息
}
