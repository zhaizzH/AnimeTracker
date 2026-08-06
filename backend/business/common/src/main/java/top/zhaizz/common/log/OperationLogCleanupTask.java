package top.zhaizz.common.log;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.pojo.entity.OperationLogEntity;

import java.time.LocalDateTime;

/**
 * operation_log 定期清理，防止无限增长。
 * ponytail: 单条 DELETE 全表扫，个人项目量级可接受；量大再改分批删
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class OperationLogCleanupTask {

    private static final int RETENTION_DAYS = 90;

    private final OperationLogMapper operationLogMapper;

    @Scheduled(cron = "0 30 3 * * ?") // 每天 03:30
    public void cleanup() {
        int deleted = operationLogMapper.delete(new LambdaQueryWrapper<OperationLogEntity>()
                .lt(OperationLogEntity::getCreatedAt, LocalDateTime.now().minusDays(RETENTION_DAYS)));
        if (deleted > 0) {
            log.info("清理 operation_log {} 条", deleted);
        }
    }
}
