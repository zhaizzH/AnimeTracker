package top.zhaizz.admin.service.impl;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.junit.jupiter.api.Test;
import top.zhaizz.common.mapper.OperationLogMapper;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.entity.OperationLogEntity;
import top.zhaizz.pojo.vo.OperationLogVO;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class AdminLogServiceImplTest {

    private final OperationLogMapper mapper = mock(OperationLogMapper.class);
    private final AdminLogServiceImpl service = new AdminLogServiceImpl(mapper);

    @Test
    void mapsPageToVO() {
        Page<OperationLogEntity> page = new Page<>(1, 20, 1);
        OperationLogEntity e = new OperationLogEntity();
        e.setId(1L);
        e.setAction("LOGIN");
        e.setModule("AUTH");
        e.setUsername("bob");
        page.setRecords(List.of(e));
        when(mapper.selectPage(any(), any())).thenReturn(page);

        PageResult<OperationLogVO> res = service.listLogs(null, null, null, null, null, null, 1, 20);

        assertThat(res.getTotal()).isEqualTo(1);
        assertThat(res.getContent()).hasSize(1);
        assertThat(res.getContent().get(0).getAction()).isEqualTo("LOGIN");
        assertThat(res.getContent().get(0).getUsername()).isEqualTo("bob");
    }
}
