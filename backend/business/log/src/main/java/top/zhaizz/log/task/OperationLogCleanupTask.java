package top.zhaizz.log.task;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import top.zhaizz.log.mapper.OperationLogMapper;
import top.zhaizz.pojo.entity.OperationLog;

import java.time.LocalDateTime;

/**
 * operation_log 定期清理，防止无限增长
 * 使用严格早于比较，保留恰好位于阈值上的记录
 */
@Component
public class OperationLogCleanupTask {

    /** 当前类的日志记录器 */
    private static final Logger log = LoggerFactory.getLogger(OperationLogCleanupTask.class);
    /** 操作日志保留天数，沿用 90 天 */
    private static final int RETENTION_DAYS = 90;

    /** 仅访问操作日志表的持久化入口 */
    private final OperationLogMapper operationLogMapper;

    /**
     * 创建操作日志清理任务
     *
     * @param operationLogMapper 仅访问操作日志表的持久化入口
     */
    public OperationLogCleanupTask(OperationLogMapper operationLogMapper) {
        this.operationLogMapper = operationLogMapper;
    }

    /** 每日清理超过保留期（90 天）的操作日志 */
    @Scheduled(cron = "0 30 3 * * ?")
    public void cleanup() {
        int deleted = operationLogMapper.delete(new LambdaQueryWrapper<top.zhaizz.pojo.entity.OperationLog>()
                .lt(OperationLog::getCreatedAt, LocalDateTime.now().minusDays(RETENTION_DAYS)));
        if (deleted > 0) {
            log.info("清理 operation_log {} 条", deleted);
        }
    }
}
