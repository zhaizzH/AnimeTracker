package top.zhaizz.log.task;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.scheduling.annotation.Scheduled;
import top.zhaizz.log.mapper.OperationLogMapper;
import top.zhaizz.pojo.entity.OperationLog;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证日志清理保留期、严格比较及原有调度时间。 */
class OperationLogCleanupTaskTest {
    /**
     * 验证只删除严格早于当前时间减 90 天的日志，保留每日 03:30 调度。
     * @throws NoSuchMethodException 清理入口缺失时使测试失败
     */
    @Test
    @SuppressWarnings({"unchecked", "rawtypes"})
    void retainsNinetyDaysAndSchedule() throws NoSuchMethodException {
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), "cleanup-test"), OperationLog.class);
        OperationLogMapper mapper = mock(OperationLogMapper.class);
        LocalDateTime before = LocalDateTime.now().minusDays(90);
        new OperationLogCleanupTask(mapper).cleanup();
        LocalDateTime after = LocalDateTime.now().minusDays(90);
        ArgumentCaptor<Wrapper> capture = ArgumentCaptor.forClass(Wrapper.class);
        verify(mapper).delete(capture.capture());
        LambdaQueryWrapper<OperationLog> filter = (LambdaQueryWrapper<OperationLog>) capture.getValue();
        assertTrue(filter.getSqlSegment().contains("created_at <"));
        assertFalse(filter.getSqlSegment().contains("<="));
        LocalDateTime cutoff = (LocalDateTime) filter.getParamNameValuePairs().values().iterator().next();
        assertFalse(cutoff.isBefore(before)); assertFalse(cutoff.isAfter(after));
        assertEquals("0 30 3 * * ?", OperationLogCleanupTask.class.getMethod("cleanup").getAnnotation(Scheduled.class).cron());
    }
}
