package top.zhaizz.admin.service;


import java.time.LocalDate;

/**
 * 日志查询服务
 */
public interface AdminLogService {

    /**
     * 分页查询操作/登录日志并返回当前筛选条件的全量聚合统计，支持按动作、模块、用户名、用户、状态与时间范围筛选
     */
    LogPageResult listLogs(String action, String module, String username, Long userId, Integer status,
                           LocalDate start, LocalDate end, int page, int size);
}
