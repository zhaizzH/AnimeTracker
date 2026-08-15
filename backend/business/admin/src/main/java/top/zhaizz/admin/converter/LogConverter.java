package top.zhaizz.admin.converter;

import top.zhaizz.pojo.entity.OperationLog;
import top.zhaizz.pojo.vo.log.LogVO;
import top.zhaizz.pojo.vo.log.OperationLogStatsVO;
import top.zhaizz.pojo.vo.log.OperationLogVO;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 操作日志转换器
 */
public class LogConverter {
    private LogConverter() {
    }

    /**
     * OperationLogEntity 实体转操作日志 VO
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
     * 组装日志分页 VO（纯转换，stats 由调用方先聚合好传入）
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
