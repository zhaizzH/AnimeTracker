package top.zhaizz.pojo.dto.log;

import top.zhaizz.pojo.entity.OperationLog;
import top.zhaizz.pojo.vo.log.OperationLogStatsVO;
import java.util.List;

/**
 * 日志查询能力返回的原始分页与全量统计，由管理端转换为展示响应
 * @param records 当前页记录，无匹配项时为空列表
 * @param total 全部匹配记录数，不受分页限制
 * @param stats 对相同筛选条件聚合的统计结果，不可为空
 */
public record LogQueryResultDTO(List<OperationLog> records, long total, OperationLogStatsVO stats) {
}
