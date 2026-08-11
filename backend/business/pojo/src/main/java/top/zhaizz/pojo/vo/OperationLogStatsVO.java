package top.zhaizz.pojo.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 操作日志统计（按当前筛选条件对全部日志聚合）
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class OperationLogStatsVO {

    /** 日志总数 */
    private Long total;
    /** 失败日志数 */
    private Long failedCount;
    /** 成功日志数 */
    private Long successCount;
    /** 平均耗时(毫秒) */
    private Long avgDurationMs;
}
