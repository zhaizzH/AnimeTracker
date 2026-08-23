package top.zhaizz.client.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.mapper.SubjectRelationMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.service.impl.ClientSubjectServiceImpl;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.vo.subject.SubjectBatchItemVO;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

/** 批量权威回查：顺序、可见性与收藏排除。 */
@ExtendWith(MockitoExtension.class)
class SubjectBatchServiceTest {

    @Mock private SubjectMapper subjectMapper;
    @Mock private SubjectTagMapper subjectTagMapper;
    @Mock private SubjectRelationMapper subjectRelationMapper;
    @Mock private CollectionMapper collectionMapper;

    private ClientSubjectServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new ClientSubjectServiceImpl(subjectMapper, subjectTagMapper, subjectRelationMapper, collectionMapper);
    }

    @Test
    void batchPreservesInputOrderAndClassifiesRejectedIds() {
        Subject visible = subject(8L, 2, false);
        Subject collected = subject(2L, 2, false);
        Subject filtered = subject(9L, 1, false);
        when(subjectMapper.selectBatchIds(List.of(8L, 2L, 9L, 404L)))
                .thenReturn(List.of(collected, filtered, visible));
        when(collectionMapper.findCollectedSubjectIds(eq(7L), anyList())).thenReturn(List.of(2L));

        var result = service.batch(List.of(8L, 2L, 9L, 404L), true, 7L);

        assertThat(result.getItems()).extracting(SubjectBatchItemVO::getId).containsExactly(8L);
        assertThat(result.getCollectedIds()).containsExactly(2L);
        assertThat(result.getFilteredIds()).containsExactly(9L);
        assertThat(result.getMissingIds()).containsExactly(404L);
        verify(subjectMapper).selectBatchIds(List.of(8L, 2L, 9L, 404L));
        verify(collectionMapper).findCollectedSubjectIds(7L, List.of(8L, 2L, 9L, 404L));
    }

    @Test
    void batchDeDuplicatesIdsAndSkipsCollectionLookupForAnonymousRequest() {
        when(subjectMapper.selectBatchIds(List.of(8L, 2L))).thenReturn(List.of(subject(2L, 2, false), subject(8L, 2, false)));

        var result = service.batch(List.of(8L, 2L, 8L), true, null);

        assertThat(result.getItems()).extracting(SubjectBatchItemVO::getId).containsExactly(8L, 2L);
        assertThat(result.getCollectedIds()).isEmpty();
        verify(subjectMapper).selectBatchIds(List.of(8L, 2L));
        verifyNoInteractions(collectionMapper);
    }

    private Subject subject(Long id, int type, boolean nsfw) {
        Subject subject = new Subject();
        subject.setId(id);
        subject.setType(type);
        subject.setNsfw(nsfw);
        subject.setName("subject-" + id);
        subject.setScore(BigDecimal.valueOf(8.5));
        return subject;
    }
}
