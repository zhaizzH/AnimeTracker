package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.OperationLogStatsVO;
import top.zhaizz.pojo.vo.OperationLogVO;

import java.time.LocalDate;

/**
 * 日志查询服务
 */
public interface AdminLogService {

    /**
     * 分页查询操作/登录日志，支持按动作、模块、用户名、用户、状态与时间范围筛选
     */
    PageResult<OperationLogVO> listLogs(String action, String module, String username, Long userId, Integer status,
                                        LocalDate start, LocalDate end, int page, int size);

    /**
     * 按当前筛选条件统计全部日志（总数/成功/失败/平均耗时）
     */
    OperationLogStatsVO stats(String action, String module, String username, Long userId, Integer status,
                              LocalDate start, LocalDate end);
}
