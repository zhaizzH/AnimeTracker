package top.zhaizz.log.service;

import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.dto.log.LogQueryResultDTO;

/** 向业务模块公开日志查询能力，调用方负责入口权限校验 */
public interface LogQueryService {
    /**
     * 查询分页记录和相同条件下的完整统计
     * @param query 已通过请求校验的条件，不可为空；缺失日期不限制对应边界
     * @return 原始记录和全量统计，无记录时列表为空且计数为零
     * @throws org.springframework.dao.DataAccessException 数据库查询失败时向调用方传播
     */
    LogQueryResultDTO query(LogQueryDTO query);
}
