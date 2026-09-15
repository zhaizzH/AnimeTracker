package top.zhaizz.log.mapper;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.toolkit.Constants;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.OperationLog;
import top.zhaizz.pojo.vo.log.OperationLogStatsVO;

/** 操作日志聚合持久化入口，仅接收日志服务构造的筛选条件 */
public interface LogStatsMapper {
    /**
     * 对完整筛选结果聚合，不受当前分页大小影响
     * @param query 与分页相同的内部查询条件，不可为空
     * @return 总量、成功数、失败数与平均毫秒耗时；无记录时各值为零
     */
    OperationLogStatsVO selectStats(@Param(Constants.WRAPPER) Wrapper<OperationLog> query);
}
