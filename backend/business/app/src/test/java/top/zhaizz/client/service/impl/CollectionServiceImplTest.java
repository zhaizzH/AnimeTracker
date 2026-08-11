package top.zhaizz.client.service.impl;

import org.junit.jupiter.api.Test;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.CollectionUpdateDTO;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.UserCollection;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class CollectionServiceImplTest {

    private final CollectionMapper mapper = mock(CollectionMapper.class);
    private final SubjectMapper subjectMapper = mock(SubjectMapper.class);
    private final CollectionServiceImpl service = new CollectionServiceImpl(mapper, subjectMapper);

    @Test
    void listCountsGroupsByType() {
        when(mapper.selectMaps(any())).thenReturn(List.of(
                Map.of("type", 1, "count", 5L),
                Map.of("type", 2, "count", 3L)
        ));

        Map<Integer, Long> counts = service.listCounts(7L);

        assertThat(counts).containsEntry(1, 5L).containsEntry(2, 3L);
    }

    @Test
    void rejectsDuplicateCollection() {
        when(subjectMapper.selectById(any())).thenReturn(new Subject());
        UserCollection existing = new UserCollection();
        existing.setType(1);
        when(mapper.selectOne(any())).thenReturn(existing);

        CollectionUpdateDTO dto = new CollectionUpdateDTO();
        dto.setType(1);

        assertThatThrownBy(() -> service.saveOrUpdate(7L, 10L, dto))
                .isInstanceOf(BizException.class)
                .extracting(e -> ((BizException) e).getCode())
                .isEqualTo(ErrorType.CONFLICT.getCode());
    }

    @Test
    void updatesRatingWhenSameTypeResubmitted() {
        when(subjectMapper.selectById(any())).thenReturn(new Subject());
        UserCollection existing = new UserCollection();
        existing.setType(1);
        existing.setRate(0);
        existing.setEpStatus(0);
        when(mapper.selectOne(any())).thenReturn(existing);

        CollectionUpdateDTO dto = new CollectionUpdateDTO();
        dto.setType(1);
        dto.setRate(8); // 修改评分，同类型重提不算重复收藏

        assertThatCode(() -> service.saveOrUpdate(7L, 10L, dto))
                .doesNotThrowAnyException();
        verify(mapper).updateById(any(UserCollection.class));
    }

    @Test
    void updatesWhenCollectionTypeDiffers() {
        when(subjectMapper.selectById(any())).thenReturn(new Subject());
        UserCollection existing = new UserCollection();
        existing.setType(1);
        when(mapper.selectOne(any())).thenReturn(existing);

        CollectionUpdateDTO dto = new CollectionUpdateDTO();
        dto.setType(3); // 换收藏状态不算重复

        assertThatCode(() -> service.saveOrUpdate(7L, 10L, dto))
                .doesNotThrowAnyException();
        verify(mapper).updateById(any(UserCollection.class));
    }
}
