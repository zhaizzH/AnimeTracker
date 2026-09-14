package top.zhaizz.log.service;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import top.zhaizz.log.mapper.LogStatsMapper;
import top.zhaizz.log.mapper.OperationLogMapper;
import top.zhaizz.log.service.impl.LogQueryServiceImpl;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.entity.OperationLog;
import top.zhaizz.pojo.vo.log.OperationLogStatsVO;
import java.time.LocalDate;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证分页与聚合使用同一参数化筛选条件及日期边界。 */
class LogQueryServiceImplTest {
    /** 为独立单元测试初始化实体列映射。 */
    @BeforeAll
    static void initializeMapping() {
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), "log-test"), OperationLog.class);
    }

    /** 验证所有筛选字段共享，结束日期转换为次日零点且严格排除。 */
    @Test
    @SuppressWarnings({"unchecked", "rawtypes"})
    void sharesAllFiltersWithStats() {
        OperationLogMapper mapper = mock(OperationLogMapper.class);
        LogStatsMapper statsMapper = mock(LogStatsMapper.class);
        LogQueryDTO query = new LogQueryDTO();
        query.setAction("LOGIN"); query.setModule("AUTH"); query.setUsername("alice");
        query.setUserId(7L); query.setStatus(0);
        query.setStart(LocalDate.of(2026, 9, 1)); query.setEnd(LocalDate.of(2026, 9, 13));
        Page<OperationLog> page = new Page<>(1, 20);
        page.setRecords(List.of(new OperationLog())); page.setTotal(5);
        when(mapper.selectPage(any(Page.class), any())).thenReturn(page);
        OperationLogStatsVO stats = new OperationLogStatsVO();
        when(statsMapper.selectStats(any())).thenReturn(stats);
        var result = new LogQueryServiceImpl(mapper, statsMapper).query(query);
        ArgumentCaptor<LambdaQueryWrapper> capture = ArgumentCaptor.forClass(LambdaQueryWrapper.class);
        verify(mapper).selectPage(any(Page.class), capture.capture());
        LambdaQueryWrapper<OperationLog> filter = capture.getValue();
        verify(statsMapper).selectStats(same(filter));
        String sql = filter.getSqlSegment();
        assertTrue(sql.contains("created_at >=")); assertTrue(sql.contains("created_at <"));
        var values = filter.getParamNameValuePairs().values();
        assertTrue(values.containsAll(List.of("LOGIN", "AUTH", "alice", 7L, 0,
                query.getStart().atStartOfDay(), query.getEnd().plusDays(1).atStartOfDay())));
        assertEquals(5, result.total()); assertSame(stats, result.stats());
    }

    /** 验证空日期和纯空白文本不生成筛选条件，也不导致空指针异常。 */
    @Test
    @SuppressWarnings({"unchecked", "rawtypes"})
    void absentDatesAndBlankTextAreUnfiltered() {
        OperationLogMapper mapper = mock(OperationLogMapper.class);
        LogStatsMapper statsMapper = mock(LogStatsMapper.class);
        when(mapper.selectPage(any(Page.class), any())).thenReturn(new Page<OperationLog>(1, 20));
        LogQueryDTO query = new LogQueryDTO(); query.setUsername("   ");
        var result = new LogQueryServiceImpl(mapper, statsMapper).query(query);
        ArgumentCaptor<LambdaQueryWrapper> capture = ArgumentCaptor.forClass(LambdaQueryWrapper.class);
        verify(statsMapper).selectStats(capture.capture());
        assertEquals("", capture.getValue().getSqlSegment());
        assertTrue(result.records().isEmpty());
    }
}
