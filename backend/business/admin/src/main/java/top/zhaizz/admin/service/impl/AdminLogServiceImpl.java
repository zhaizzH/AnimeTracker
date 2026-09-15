package top.zhaizz.admin.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.admin.converter.LogConverter;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.log.service.LogQueryService;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.dto.log.LogQueryResultDTO;
import top.zhaizz.pojo.vo.log.LogVO;

/** 管理端日志用例，仅通过公开查询服务获取数据并转换响应 */
@Service
@RequiredArgsConstructor
public class AdminLogServiceImpl implements AdminLogService {
    /** 封装分页、统计和数据库访问的日志公开能力 */
    private final LogQueryService logQueryService;

    /**
     * 查询管理员请求的日志并组装管理端展示对象
     * @param request 已校验的筛选与分页参数，不可为空
     * @return 分页日志与全量统计，无匹配项时内容列表为空
     * @throws org.springframework.dao.DataAccessException 查询失败时传播，不伪造空列表
     */
    @Override
    public LogVO listLogs(LogQueryDTO request) {
        LogQueryResultDTO result = logQueryService.query(request);
        return LogConverter.toLogVO(result.records(), result.total(),
                request.getPage(), request.getSize(), result.stats());
    }
}
