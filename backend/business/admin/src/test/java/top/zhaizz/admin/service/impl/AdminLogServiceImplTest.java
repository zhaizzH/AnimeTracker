package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.admin.mapper.AdminLogMapper;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.entity.OperationLog;
import top.zhaizz.pojo.vo.log.OperationLogStatsVO;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 日志筛选条件构建测试：空日期不得 NPE，且分页/统计共用同一套日期语义
 */
@ExtendWith(MockitoExtension.class)
class AdminLogServiceImplTest {

    static {
        // 单元测试无 Spring 容器，手动注册实体列缓存，使 LambdaQueryWrapper.getSqlSegment() 可用
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), OperationLog.class);
    }

    @Mock
    private OperationLogMapper operationLogMapper;
    @Mock
    private AdminLogMapper adminLogMapper;

    private AdminLogServiceImpl service;

    private static final LocalDateTime START_DAY_START = LocalDateTime.of(2026, 8, 1, 0, 0);
    private static final LocalDateTime END_EXCLUSIVE = LocalDateTime.of(2026, 8, 11, 0, 0);

    @BeforeEach
    void setUp() {
        service = new AdminLogServiceImpl(operationLogMapper, adminLogMapper);
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private LambdaQueryWrapper<OperationLog> captureWrapper(LogQueryDTO q) {
        when(operationLogMapper.selectPage(any(), any())).thenAnswer(inv -> inv.getArgument(0));
        when(adminLogMapper.selectStats(any())).thenReturn(new OperationLogStatsVO());
        service.listLogs(q);
        ArgumentCaptor<LambdaQueryWrapper<OperationLog>> captor = ArgumentCaptor.forClass(LambdaQueryWrapper.class);
        verify(operationLogMapper).selectPage(any(), captor.capture());
        return captor.getValue();
    }

    @Test
    void allEmptyDatesAddsNoDateCondition() {
        LogQueryDTO q = new LogQueryDTO();
        LambdaQueryWrapper<OperationLog> wrapper = captureWrapper(q);
        assertThat(wrapper.getSqlSegment().toLowerCase()).doesNotContain("created_at");
        assertThat(wrapper.getParamNameValuePairs().values()).isEmpty();
    }

    @Test
    void startOnlyAddsLowerBound() {
        LogQueryDTO q = new LogQueryDTO();
        q.setStart(java.time.LocalDate.of(2026, 8, 1));
        LambdaQueryWrapper<OperationLog> wrapper = captureWrapper(q);
        assertThat(wrapper.getSqlSegment().toLowerCase())
                .contains("created_at >=")
                .doesNotContain("created_at <");
        assertThat(wrapper.getParamNameValuePairs().values()).contains(START_DAY_START);
    }

    @Test
    void endOnlyAddsExclusiveUpperBound() {
        LogQueryDTO q = new LogQueryDTO();
        q.setEnd(java.time.LocalDate.of(2026, 8, 10));
        LambdaQueryWrapper<OperationLog> wrapper = captureWrapper(q);
        assertThat(wrapper.getSqlSegment().toLowerCase())
                .contains("created_at <")
                .doesNotContain("created_at >=");
        assertThat(wrapper.getParamNameValuePairs().values()).contains(END_EXCLUSIVE);
    }

    @Test
    void fullRangeAddsInclusiveStartAndExclusiveNextDayEnd() {
        LogQueryDTO q = new LogQueryDTO();
        q.setStart(java.time.LocalDate.of(2026, 8, 1));
        q.setEnd(java.time.LocalDate.of(2026, 8, 10));
        LambdaQueryWrapper<OperationLog> wrapper = captureWrapper(q);
        assertThat(wrapper.getSqlSegment().toLowerCase())
                .contains("created_at >=")
                .contains("created_at <");
        assertThat(wrapper.getParamNameValuePairs().values())
                .contains(START_DAY_START, END_EXCLUSIVE);
    }

    @Test
    void paginationAndStatsShareSameFilterSemantics() {
        LogQueryDTO q = new LogQueryDTO();
        q.setStart(java.time.LocalDate.of(2026, 8, 1));
        q.setEnd(java.time.LocalDate.of(2026, 8, 10));
        captureWrapper(q);

        // 分页条件：含开始日期当日 0 点，不含结束日期的次日 0 点
        // 统计查询(XML: created_at >= #{start}, created_at < DATE_ADD(#{end}, INTERVAL 1 DAY)) 使用相同语义
        verify(adminLogMapper).selectStats(q);
    }
}
