package top.zhaizz.admin.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.mapper.OperationLogMapper;

import java.time.LocalDate;

/**
 * 日志查询服务实现
 */
@Service
@RequiredArgsConstructor
public class AdminLogServiceImpl implements AdminLogService {

    private final OperationLogMapper operationLogMapper;

    @Override
    public LogPageResult listLogs(String action, String module, String username, Long userId, Integer status,
                                  LocalDate start, LocalDate end, int page, int size) {
        return null;
    }
}
