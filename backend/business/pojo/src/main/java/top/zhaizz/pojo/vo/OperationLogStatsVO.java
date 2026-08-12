package top.zhaizz.pojo.vo;

import lombok.Data;

/**
 * 操作日志统计（按当前筛选条件对全部日志聚合）
 */
@Data
public class OperationLogStatsVO {

    private Long total;          // 日志总数
    private Long failedCount;    // 失败日志数
    private Long successCount;   // 成功日志数
    private Long avgDurationMs;  // 平均耗时(毫秒)
}
