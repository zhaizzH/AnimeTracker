package top.zhaizz.pojo.vo.log;

import lombok.Data;

import java.util.List;

/**
 * 日志分页结果
 */
@Data
public class LogVO {

    private List<OperationLogVO> content;   // 当前页日志明细
    private long total;                     // 匹配筛选条件的日志总数(分页)
    private int page;                       // 当前页码
    private int size;                       // 每页条数
    private OperationLogStatsVO stats;      // 当前筛选条件下全量聚合统计
}
