package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.vo.log.LogVO;

/**
 * 日志查询服务
 */
public interface AdminLogService {

    /**
     * 分页查询操作/登录日志并返回当前筛选条件的全量聚合统计，支持按动作、模块、用户名、用户、状态与时间范围筛选
     */
    PageResult<LogVO> listLogs(LogQueryDTO request);
}
