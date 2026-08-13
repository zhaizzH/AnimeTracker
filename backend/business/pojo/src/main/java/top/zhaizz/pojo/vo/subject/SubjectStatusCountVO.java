package top.zhaizz.pojo.vo.subject;

import lombok.Data;

/**
 * 导入状态分布
 */
@Data
public class SubjectStatusCountVO {
    private Integer importStatus;   // 导入状态: 0=待导入, 1=已导入
    private long count;             // 该状态条目数
}
