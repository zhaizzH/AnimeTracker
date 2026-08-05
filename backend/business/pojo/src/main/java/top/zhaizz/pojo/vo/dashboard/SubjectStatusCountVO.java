package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 导入状态分布
 */
@Data
public class SubjectStatusCountVO {
    private Integer importStatus;   // 0=待导入, 1=已导入
    private long count;
}
