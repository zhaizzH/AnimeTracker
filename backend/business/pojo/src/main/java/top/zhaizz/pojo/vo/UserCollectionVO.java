package top.zhaizz.pojo.vo;

import lombok.Data;

@Data
public class UserCollectionVO {

    private Long id;
    private Long subjectId;
    private Integer type;
    private Integer rate;
    private Integer epStatus;
    private SubjectListVO subject;
}
