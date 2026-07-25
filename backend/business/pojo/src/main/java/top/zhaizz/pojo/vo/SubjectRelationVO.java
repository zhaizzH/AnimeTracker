package top.zhaizz.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 条目关联视图
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SubjectRelationVO {

    private String relation;
    private SubjectListVO relatedSubject;
}
