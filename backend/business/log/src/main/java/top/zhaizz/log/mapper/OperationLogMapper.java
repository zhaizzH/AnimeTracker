package top.zhaizz.log.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import top.zhaizz.pojo.entity.OperationLog;

/**
 * 操作日志持久化入口，仅由日志模块内部使用。
 */
public interface OperationLogMapper extends BaseMapper<OperationLog> {
}
