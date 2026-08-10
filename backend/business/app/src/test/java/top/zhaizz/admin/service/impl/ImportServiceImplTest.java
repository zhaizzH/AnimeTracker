package top.zhaizz.admin.service.impl;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.vo.ImportStatusVO;

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
    private final ImportServiceImpl service = new ImportServiceImpl(restTemplate, agentProperties);

    private static final String URL = "http://agent-base/api/admin/agent/import/run?mode=season&key=2026-summer&workers=3";
    private static final String URL_RECENT = "http://agent-base/api/admin/agent/import/run?mode=recent";
    private static final String STATUS_URL = "http://agent-base/api/admin/agent/import/status";

    @Test
    void forwardsValidRunToAgent() {
        agentProperties.setBaseUrl("http://agent-base");
        assertThatCode(() -> service.runImport("Bearer t", "season", "2026-summer", null, 3))
                .doesNotThrowAnyException();
        verify(restTemplate).exchange(eq(URL), eq(HttpMethod.POST), any(), eq(String.class));
    }

    @Test
    void rejectsInvalidModeBeforeForwarding() {
        agentProperties.setBaseUrl("http://agent-base");
        assertThatThrownBy(() -> service.runImport("Bearer t", "bogus", null, null, null))
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
        assertThatThrownBy(() -> service.runImport("Bearer t", "recent", null, null, null))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.CONFLICT.getCode());
    }

    @Test
    void mapsConnectionFailureToInternalError() {
        agentProperties.setBaseUrl("http://agent-base");
        when(restTemplate.exchange(eq(URL_RECENT), eq(HttpMethod.POST), any(), eq(String.class)))
                .thenThrow(new ResourceAccessException("connect refused"));
        assertThatThrownBy(() -> service.runImport("Bearer t", "recent", null, null, null))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.INTERNAL_ERROR.getCode());
    }

    @Test
    void forwardsStatusToAgent() {
        agentProperties.setBaseUrl("http://agent-base");
        ImportStatusVO vo = new ImportStatusVO();
        vo.setTotalSubjects(42);
        when(restTemplate.exchange(eq(STATUS_URL), eq(HttpMethod.GET), any(HttpEntity.class), eq(ImportStatusVO.class)))
                .thenReturn(ResponseEntity.ok(vo));
        assertThat(service.getImportStatus("Bearer t")).isSameAs(vo);
        verify(restTemplate).exchange(eq(STATUS_URL), eq(HttpMethod.GET), any(HttpEntity.class), eq(ImportStatusVO.class));
    }

    @Test
    void mapsStatusConnectionFailureToInternalError() {
        agentProperties.setBaseUrl("http://agent-base");
        when(restTemplate.exchange(eq(STATUS_URL), eq(HttpMethod.GET), any(HttpEntity.class), eq(ImportStatusVO.class)))
                .thenThrow(new ResourceAccessException("connect refused"));
        assertThatThrownBy(() -> service.getImportStatus("Bearer t"))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.INTERNAL_ERROR.getCode());
    }
}
