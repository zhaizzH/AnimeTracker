package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import top.zhaizz.admin.converter.LogConverter;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.entity.OperationLogEntity;
import top.zhaizz.pojo.vo.OperationLogStatsVO;
import top.zhaizz.pojo.vo.OperationLogVO;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 日志查询服务实现
 */
@Service
@RequiredArgsConstructor
public class AdminLogServiceImpl implements AdminLogService {

    private final OperationLogMapper operationLogMapper;

    @Override
    public PageResult<OperationLogVO> listLogs(String action, String module, String username, Long userId, Integer status,
                                               LocalDate start, LocalDate end, int page, int size) {
        QueryWrapper<OperationLogEntity> qw = buildQuery(action, module, username, userId, status, start, end)
                .orderByDesc("created_at");
        Page<OperationLogEntity> p = operationLogMapper.selectPage(new Page<>(page, size), qw);
        List<OperationLogVO> records = p.getRecords().stream().map(LogConverter::toVO).toList();
        return PageResult.of(records, p.getTotal(), (int) p.getCurrent(), (int) p.getSize());
    }

    @Override
    public OperationLogStatsVO stats(String action, String module, String username, Long userId, Integer status,
                                     LocalDate start, LocalDate end) {
        QueryWrapper<OperationLogEntity> qw = buildQuery(action, module, username, userId, status, start, end)
                .select(
                        "COUNT(*) AS total",
                        "SUM(CASE WHEN status <> 0 THEN 1 ELSE 0 END) AS failedCount",
                        "COALESCE(AVG(duration_ms), 0) AS avgDurationMs");
        List<Map<String, Object>> rows = operationLogMapper.selectMaps(qw);
        Map<String, Object> row = rows.isEmpty() ? Map.of() : rows.get(0);
        long total = toLong(row.get("total"));
        long failed = toLong(row.get("failedCount"));
        long avg = toLong(row.get("avgDurationMs"));
        return new OperationLogStatsVO(total, failed, total - failed, avg);
    }

    private long toLong(Object value) {
        return value == null ? 0L : ((Number) value).longValue();
    }

    private QueryWrapper<OperationLogEntity> buildQuery(String action, String module, String username, Long userId,
                                                        Integer status, LocalDate start, LocalDate end) {
        return new QueryWrapper<OperationLogEntity>()
                .eq(StringUtils.hasText(action), "action", action)
                .eq(StringUtils.hasText(module), "module", module)
                .like(StringUtils.hasText(username), "username", username)
                .eq(userId != null, "user_id", userId)
                .eq(status != null, "status", status)
                .ge(start != null, "created_at", start != null ? start.atStartOfDay() : null)
                .lt(end != null, "created_at", end != null ? end.plusDays(1).atStartOfDay() : null);
    }
}
