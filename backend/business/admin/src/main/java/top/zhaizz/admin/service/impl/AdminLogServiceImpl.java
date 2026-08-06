package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import top.zhaizz.admin.converter.LogConverter;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.entity.OperationLogEntity;
import top.zhaizz.pojo.vo.OperationLogVO;

import java.time.LocalDate;
import java.util.List;

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
        LambdaQueryWrapper<OperationLogEntity> qw = new LambdaQueryWrapper<OperationLogEntity>()
                .eq(StringUtils.hasText(action), OperationLogEntity::getAction, action)
                .eq(StringUtils.hasText(module), OperationLogEntity::getModule, module)
                .like(StringUtils.hasText(username), OperationLogEntity::getUsername, username)
                .eq(userId != null, OperationLogEntity::getUserId, userId)
                .eq(status != null, OperationLogEntity::getStatus, status)
                .ge(start != null, OperationLogEntity::getCreatedAt, start != null ? start.atStartOfDay() : null)
                .lt(end != null, OperationLogEntity::getCreatedAt, end != null ? end.plusDays(1).atStartOfDay() : null)
                .orderByDesc(OperationLogEntity::getCreatedAt);
        Page<OperationLogEntity> p = operationLogMapper.selectPage(new Page<>(page, size), qw);
        List<OperationLogVO> records = p.getRecords().stream().map(LogConverter::toVO).toList();
        return PageResult.of(records, p.getTotal(), (int) p.getCurrent(), (int) p.getSize());
    }
}
