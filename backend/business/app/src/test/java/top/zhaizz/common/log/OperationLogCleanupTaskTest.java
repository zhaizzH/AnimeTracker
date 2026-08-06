package top.zhaizz.common.log;

import org.junit.jupiter.api.Test;
import top.zhaizz.common.mapper.OperationLogMapper;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class OperationLogCleanupTaskTest {

    @Test
    void deletesOldLogs() {
        OperationLogMapper mapper = mock(OperationLogMapper.class);
        when(mapper.delete(any())).thenReturn(3);

        new OperationLogCleanupTask(mapper).cleanup();

        verify(mapper).delete(any());
    }
}
