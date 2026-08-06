package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.OperationLogVO;

import java.time.LocalDate;

/**
 * 日志查询服务
 */
public interface AdminLogService {
    PageResult<OperationLogVO> listLogs(String action, String module, String username, Long userId, Integer status,
                                        LocalDate start, LocalDate end, int page, int size);
}
