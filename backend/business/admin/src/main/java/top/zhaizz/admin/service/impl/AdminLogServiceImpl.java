package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.pojo.dto.LogQueryDTO;
import top.zhaizz.pojo.entity.OperationLogEntity;
import top.zhaizz.pojo.vo.LogPageVO;
import top.zhaizz.pojo.vo.OperationLogStatsVO;
import top.zhaizz.pojo.vo.OperationLogVO;

import java.util.Map;

/**
 * 日志查询服务实现
 */
@Service
@RequiredArgsConstructor
public class AdminLogServiceImpl implements AdminLogService {

    private final OperationLogMapper operationLogMapper;

    @Override
    public LogPageVO listLogs(LogQueryDTO dto) {
        QueryWrapper<OperationLogEntity> pageWrapper = buildWrapper(dto);
        pageWrapper.orderByDesc("created_at");
        Page<OperationLogEntity> page = operationLogMapper.selectPage(new Page<>(dto.getPage(), dto.getSize()), pageWrapper);

        Map<String, Object> row = operationLogMapper.selectMaps(buildWrapper(dto).select(
                "COUNT(*) AS total",
                "COALESCE(SUM(status = 1),0) AS failedCount",
                "COALESCE(AVG(duration_ms),0) AS avgDurationMs")).get(0);
        long total = ((Number) row.get("total")).longValue();
        long failed = ((Number) row.get("failedCount")).longValue();

        OperationLogStatsVO stats = new OperationLogStatsVO();
        stats.setTotal(total);
        stats.setFailedCount(failed);
        stats.setSuccessCount(total - failed);
        stats.setAvgDurationMs(((Number) row.get("avgDurationMs")).longValue());

        LogPageVO vo = new LogPageVO();
        vo.setTotal(page.getTotal());
        vo.setPage(dto.getPage());
        vo.setSize(dto.getSize());
        vo.setContent(page.getRecords().stream().map(this::toVO).toList());
        vo.setStats(stats);
        return vo;
    }

    private QueryWrapper<OperationLogEntity> buildWrapper(LogQueryDTO dto) {
        QueryWrapper<OperationLogEntity> w = new QueryWrapper<>();
        w.eq(dto.getAction() != null, "action", dto.getAction());
        w.eq(dto.getModule() != null, "module", dto.getModule());
        w.eq(dto.getUsername() != null, "username", dto.getUsername());
        w.eq(dto.getUserId() != null, "user_id", dto.getUserId());
        w.eq(dto.getStatus() != null, "status", dto.getStatus());
        if (dto.getStart() != null) {
            w.ge("created_at", dto.getStart().atStartOfDay());
        }
        if (dto.getEnd() != null) {
            w.lt("created_at", dto.getEnd().plusDays(1).atStartOfDay());
        }
        return w;
    }

    private OperationLogVO toVO(OperationLogEntity e) {
        OperationLogVO vo = new OperationLogVO();
        vo.setId(e.getId());
        vo.setUserId(e.getUserId());
        vo.setUsername(e.getUsername());
        vo.setAction(e.getAction());
        vo.setModule(e.getModule());
        vo.setMethod(e.getMethod());
        vo.setPath(e.getPath());
        vo.setIp(e.getIp());
        vo.setUserAgent(e.getUserAgent());
        vo.setStatus(e.getStatus());
        vo.setErrorMsg(e.getErrorMsg());
        vo.setDurationMs(e.getDurationMs());
        vo.setCreatedAt(e.getCreatedAt());
        return vo;
    }
}
