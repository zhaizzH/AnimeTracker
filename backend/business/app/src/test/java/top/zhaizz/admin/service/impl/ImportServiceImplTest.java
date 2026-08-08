package top.zhaizz.admin.service.impl;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.exception.BizException;

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
    private final ImportRecordMapper mapper = mock(ImportRecordMapper.class);
    private final ImportServiceImpl service = new ImportServiceImpl(restTemplate, agentProperties, mapper);

    private static final String URL = "http://agent-base/api/admin/agent/import/run";

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
        when(restTemplate.exchange(eq(URL), eq(HttpMethod.POST), any(), eq(String.class)))
                .thenThrow(new HttpClientErrorException(HttpStatus.CONFLICT, "已有导入任务运行中"));
        assertThatThrownBy(() -> service.runImport("Bearer t", "recent", null, null, null))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.CONFLICT.getCode());
    }

    @Test
    void mapsConnectionFailureToInternalError() {
        agentProperties.setBaseUrl("http://agent-base");
        when(restTemplate.exchange(eq(URL), eq(HttpMethod.POST), any(), eq(String.class)))
                .thenThrow(new ResourceAccessException("connect refused"));
        assertThatThrownBy(() -> service.runImport("Bearer t", "recent", null, null, null))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.INTERNAL_ERROR.getCode());
    }
}
