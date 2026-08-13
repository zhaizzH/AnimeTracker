package top.zhaizz.admin.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.vo.log.LogVO;

/**
 * 日志查询服务实现
 */
@Service
@RequiredArgsConstructor
public class AdminLogServiceImpl implements AdminLogService {

    private final OperationLogMapper operationLogMapper;

    @Override
    public PageResult<LogVO> listLogs(LogQueryDTO request) {
        return null;
    }
}
