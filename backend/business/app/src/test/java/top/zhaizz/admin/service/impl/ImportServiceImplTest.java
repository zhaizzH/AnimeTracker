package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.imprt.ImportRecordQueryDTO;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;
import top.zhaizz.pojo.entity.ImportRecord;
import top.zhaizz.pojo.vo.imprt.ImportRecordVO;
import top.zhaizz.pojo.vo.imprt.ImportStatusVO;

import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class ImportServiceImplTest {

    private final RestTemplate restTemplate = mock(RestTemplate.class);
    private final AgentProperties agentProperties = new AgentProperties();
    private final ImportRecordMapper importRecordMapper = mock(ImportRecordMapper.class);
    private final ImportServiceImpl service =
            new ImportServiceImpl(restTemplate, agentProperties, importRecordMapper);

    private static final String URL = "http://agent-base/api/admin/agent/import/run?mode=season&key=2026-summer&workers=3";
    private static final String URL_RECENT = "http://agent-base/api/admin/agent/import/run?mode=recent";

    private static ImportRecord completed() {
        ImportRecord e = new ImportRecord();
        e.setId(1L);
        e.setSeasonKey("2026-summer");
        e.setStatus("COMPLETED");
        e.setSubjectCount(7);
        e.setStartedAt(LocalDateTime.of(2026, 8, 1, 10, 0, 0));
        e.setCompletedAt(LocalDateTime.of(2026, 8, 1, 10, 5, 0));
        return e;
    }

    @Test
    void forwardsValidRunToAgent() {
        agentProperties.setBaseUrl("http://agent-base");
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("season");
        request.setKey("2026-summer");
        request.setWorkers(3);
        assertThatCode(() -> service.runImport("Bearer t", request))
                .doesNotThrowAnyException();
        verify(restTemplate).exchange(eq(URL), eq(HttpMethod.POST), any(), eq(String.class));
    }

    @Test
    void rejectsInvalidModeBeforeForwarding() {
        agentProperties.setBaseUrl("http://agent-base");
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("bogus");
        assertThatThrownBy(() -> service.runImport("Bearer t", request))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.BAD_REQUEST.getCode());
        verifyNoInteractions(restTemplate);
    }

    @Test
    void mapsConflictToBizException() {
        agentProperties.setBaseUrl("http://agent-base");
        when(restTemplate.exchange(eq(URL_RECENT), eq(HttpMethod.POST), any(), eq(String.class)))
                .thenThrow(new HttpClientErrorException(HttpStatus.CONFLICT, "已有导入任务运行中"));
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("recent");
        assertThatThrownBy(() -> service.runImport("Bearer t", request))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.CONFLICT.getCode());
    }

    @Test
    void mapsConnectionFailureToInternalError() {
        agentProperties.setBaseUrl("http://agent-base");
        when(restTemplate.exchange(eq(URL_RECENT), eq(HttpMethod.POST), any(), eq(String.class)))
                .thenThrow(new ResourceAccessException("connect refused"));
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("recent");
        assertThatThrownBy(() -> service.runImport("Bearer t", request))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.INTERNAL_ERROR.getCode());
    }

    @Test
    void readsStatusFromDb() {
        ImportRecord running = new ImportRecord();
        running.setId(2L);
        running.setStatus("RUNNING");
        running.setStartedAt(LocalDateTime.of(2026, 8, 2, 10, 0, 0)); // 更近，排在最前
        ImportRecord completed = completed();

        when(importRecordMapper.selectCount(null)).thenReturn(3L);      // 总日志数
        when(importRecordMapper.selectCount(any())).thenReturn(3L);     // 按状态统计（COMPLETED/FAILED）
        when(importRecordMapper.selectList(any())).thenReturn(List.of(running, completed));

        ImportStatusVO vo = service.getImportStatus();

        // 卡片1: 当前导入日志数量 = import_record 全量记录数（回归: 2026-08-11 误显示 subject+episode 条目总数）
        assertThat(vo.getTotalLogs()).isEqualTo(3L);
        // 成功/失败任务数为全量统计，而非 recentRecords 窗口内过滤（回归: 2026-08-11 只显示最近10条内数量）
        assertThat(vo.getCompletedCount()).isEqualTo(3L);
        assertThat(vo.getFailedCount()).isEqualTo(3L);
        assertThat(vo.getRecentRecords()).hasSize(2);
        assertThat(vo.getRecentRecords().get(0).getSeason()).isNull(); // running 无季度
        assertThat(vo.getLastImportedAt()).isEqualTo(LocalDateTime.of(2026, 8, 1, 10, 5, 0));
    }

    @Test
    void readsRecordsFromDb() {
        Page<ImportRecord> page = new Page<>(2, 10);
        page.setRecords(List.of(completed()));
        page.setTotal(3);
        when(importRecordMapper.selectPage(any(), any())).thenReturn(page);

        ImportRecordQueryDTO request = new ImportRecordQueryDTO();
        request.setPage(2);
        request.setSize(10);
        request.setStatus("FAILED");
        PageResult<ImportRecordVO> result = service.getImportRecords(request);

        assertThat(result.getPage()).isEqualTo(2);
        assertThat(result.getSize()).isEqualTo(10);
        assertThat(result.getTotal()).isEqualTo(3L);
        assertThat(result.getContent()).hasSize(1);
        ImportRecordVO vo = result.getContent().get(0);
        assertThat(vo.getSeason()).isEqualTo("2026-summer");
        assertThat(vo.getStatus()).isEqualTo("COMPLETED");
        assertThat(vo.getSubjectCount()).isEqualTo(7);
    }
}
