package top.zhaizz.admin.converter;

import top.zhaizz.pojo.entity.OperationLog;
import top.zhaizz.pojo.vo.log.LogVO;
import top.zhaizz.pojo.vo.log.OperationLogStatsVO;
import top.zhaizz.pojo.vo.log.OperationLogVO;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 操作日志转换器。
 */
public class LogConverter {
    /** 禁止实例化无状态日志转换器。 */
    private LogConverter() {
    }

    /**
     * 按原字段映射生成管理端日志对象，不修改实体。
     * @param e 日志实体，不可为空
     * @return 新的展示对象，可空字段原样保留
     * @throws NullPointerException 实体为空时抛出
     */
    public static OperationLogVO toVO(OperationLog e) {
        OperationLogVO vo = new OperationLogVO();
        vo.setId(e.getId());
        vo.setUserId(e.getUserId());
        vo.setUsername(e.getUsername());
        vo.setAction(e.getAction());
        vo.setModule(e.getModule());
        vo.setMethod(e.getMethod());
        vo.setPath(e.getPath());
        vo.setParams(e.getParams());
        vo.setIp(e.getIp());
        vo.setUserAgent(e.getUserAgent());
        vo.setStatus(e.getStatus());
        vo.setErrorMsg(e.getErrorMsg());
        vo.setDurationMs(e.getDurationMs());
        vo.setCreatedAt(e.getCreatedAt());
        return vo;
    }

    /**
     * 组装日志分页响应，保留输入记录顺序，统计由调用方提供。
     * @param records 当前页实体列表，不可为空且不能包含空元素
     * @param total 全量匹配记录数
     * @param page 当前页码，从 1 开始
     * @param size 每页条数
     * @param stats 聚合结果，原样引用，不在转换器查询数据库
     * @return 新的分页对象；空记录列表转换为空内容列表
     * @throws NullPointerException 记录列表或其中元素为空时抛出
     */
    public static LogVO toLogVO(List<OperationLog> records, long total, int page, int size,
                                OperationLogStatsVO stats) {
        LogVO vo = new LogVO();
        vo.setContent(records.stream().map(LogConverter::toVO).collect(Collectors.toList()));
        vo.setTotal(total);
        vo.setPage(page);
        vo.setSize(size);
        vo.setStats(stats);
        return vo;
    }
}
