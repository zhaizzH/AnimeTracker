package top.zhaizz.admin.service.impl;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.admin.gateway.ImportAgentGateway;
import top.zhaizz.admin.mapper.ImportRecordMapper;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

@ExtendWith(MockitoExtension.class)
class ImportServiceImplTest {
    @Mock
    ImportAgentGateway importAgentGateway;
    @Mock
    ImportRecordMapper importRecordMapper;

    private ImportServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new ImportServiceImpl(importAgentGateway, importRecordMapper);
    }

    @Test
    void validRequestDelegatesToImportAgentGateway() {
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("season");
        request.setKey("2026-summer");

        service.runImport("Bearer token", request);

        verify(importAgentGateway).runImport("Bearer token", request);
    }

    @Test
    void sinceModeWithoutDateFailsBeforeCallingGateway() {
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("since");

        BizException error = assertThrows(BizException.class,
                () -> service.runImport("Bearer token", request));

        assertThat(error.getCode()).isEqualTo(ErrorType.BAD_REQUEST.getCode());
        assertThat(error.getMessage()).isEqualTo("since 模式需要 since");
        verifyNoInteractions(importAgentGateway);
    }
}
