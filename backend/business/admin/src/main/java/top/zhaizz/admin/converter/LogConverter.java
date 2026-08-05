package top.zhaizz.admin.converter;

import top.zhaizz.pojo.entity.OperationLogEntity;
import top.zhaizz.pojo.vo.OperationLogVO;

/**
 * 操作日志转换器
 */
public class LogConverter {
    private LogConverter() {
    }

    public static OperationLogVO toVO(OperationLogEntity e) {
        OperationLogVO vo = new OperationLogVO();
        vo.setId(e.getId());
        vo.setUserId(e.getUserId());
        vo.setUsername(e.getUsername());
        vo.setAction(e.getAction());
        vo.setModule(e.getModule());
        vo.setMethod(e.getMethod());
        vo.setPath(e.getPath());
        vo.setIp(e.getIp());
        vo.setUserAgent(e.getUserAgent());
        vo.setStatus(e.getStatus());
        vo.setErrorMsg(e.getErrorMsg());
        vo.setDurationMs(e.getDurationMs());
        vo.setCreatedAt(e.getCreatedAt());
        return vo;
    }
}
