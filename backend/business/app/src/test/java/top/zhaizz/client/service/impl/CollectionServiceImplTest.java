package top.zhaizz.client.service.impl;

import org.junit.jupiter.api.Test;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class CollectionServiceImplTest {

    private final CollectionMapper mapper = mock(CollectionMapper.class);
    private final CollectionServiceImpl service = new CollectionServiceImpl(mapper, mock(SubjectMapper.class));

    @Test
    void listCountsGroupsByType() {
        when(mapper.selectMaps(any())).thenReturn(List.of(
                Map.of("type", 1, "count", 5L),
                Map.of("type", 2, "count", 3L)
        ));

        Map<Integer, Long> counts = service.listCounts(7L);

        assertThat(counts).containsEntry(1, 5L).containsEntry(2, 3L);
    }
}
