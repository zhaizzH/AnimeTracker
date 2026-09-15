package top.zhaizz.log.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import top.zhaizz.log.mapper.OperationLogMapper;
import top.zhaizz.log.mapper.LogStatsMapper;
import top.zhaizz.log.service.LogQueryService;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.dto.log.LogQueryResultDTO;
import top.zhaizz.pojo.entity.OperationLog;

/** 使用同一参数化条件完成日志分页和统计，防止筛选口径分叉 */
@Service
@RequiredArgsConstructor
public class LogQueryServiceImpl implements LogQueryService {
    /** 日志分页与存储访问入口 */
    private final OperationLogMapper operationLogMapper;
    /** 完整筛选结果的聚合访问入口 */
    private final LogStatsMapper logStatsMapper;

    /** {@inheritDoc} */
    @Override
    public LogQueryResultDTO query(LogQueryDTO query) {
        LambdaQueryWrapper<OperationLog> filter = buildWrapper(query);
        Page<OperationLog> page = operationLogMapper.selectPage(
                new Page<>(query.getPage(), query.getSize()), filter);
        return new LogQueryResultDTO(page.getRecords(), page.getTotal(), logStatsMapper.selectStats(filter));
    }

    /**
     * 构建日志分页筛选条件，筛选逻辑需与 统计查询 保持同步
     * 日期条件用显式 if 添加，避免空日期在条件求值前被提前解引用导致 NPE
     * @param q 已校验的查询条件，不可为空
     * @return 参数化筛选条件，结束日期使用次日零点的严格小于比较
     */
    private LambdaQueryWrapper<OperationLog> buildWrapper(LogQueryDTO q) {
        LambdaQueryWrapper<OperationLog> wrapper = Wrappers.<OperationLog>lambdaQuery()
                .eq(StringUtils.hasText(q.getAction()), OperationLog::getAction, q.getAction())
                .eq(StringUtils.hasText(q.getModule()), OperationLog::getModule, q.getModule())
                .eq(StringUtils.hasText(q.getUsername()), OperationLog::getUsername, q.getUsername())
                .eq(q.getUserId() != null, OperationLog::getUserId, q.getUserId())
                .eq(q.getStatus() != null, OperationLog::getStatus, q.getStatus());
        if (q.getStart() != null) {
            wrapper.ge(OperationLog::getCreatedAt, q.getStart().atStartOfDay());
        }
        if (q.getEnd() != null) {
            wrapper.lt(OperationLog::getCreatedAt, q.getEnd().plusDays(1).atStartOfDay());
        }
        return wrapper;
    }
}
