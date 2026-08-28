package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import top.zhaizz.admin.converter.LogConverter;
import top.zhaizz.admin.mapper.AdminLogMapper;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.entity.OperationLog;
import top.zhaizz.pojo.vo.log.LogVO;

/**
 * 日志查询服务实现
 */
@Service
@RequiredArgsConstructor
public class AdminLogServiceImpl implements AdminLogService {

    private final OperationLogMapper operationLogMapper;
    private final AdminLogMapper adminLogMapper;

    @Override
    public LogVO listLogs(LogQueryDTO request) {
        Page<OperationLog> page = operationLogMapper.selectPage(
                new Page<>(request.getPage(), request.getSize()), buildWrapper(request));
        return LogConverter.toLogVO(page.getRecords(), page.getTotal(),
                request.getPage(), request.getSize(), adminLogMapper.selectStats(request));
    }

    /**
     * 构建日志分页筛选条件，筛选逻辑需与 AdminLogMapper.selectStats 的 SQL 保持同步。
     * 日期条件用显式 if 添加，避免空日期在条件求值前被提前解引用导致 NPE。
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
