package top.zhaizz.admin.mapper;

import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.vo.log.OperationLogStatsVO;

/**
 * 操作日志聚合查询 Mapper
 */
public interface AdminLogMapper {

    /**
     * 按筛选条件对全部日志做聚合统计（总数/成功/失败/平均耗时）
     */
    OperationLogStatsVO selectStats(@Param("q") LogQueryDTO q);
}
