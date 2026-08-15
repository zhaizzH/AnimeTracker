package top.zhaizz.client.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.client.mapper.CollectionProgressMapper;
import top.zhaizz.client.model.CollectionProgressCandidate;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 本周追番进度候选项计算测试
 */
@ExtendWith(MockitoExtension.class)
class CollectionProgressCalculatorTest {

    private static final LocalDate MONDAY = LocalDate.of(2026, 8, 10);
    private static final LocalDate FRIDAY = LocalDate.of(2026, 8, 14);

    @Mock
    private CollectionProgressMapper mapper;

    @InjectMocks
    private CollectionProgressCalculator calculator;

    @Test
    void keepsOnlyCandidatesWhoseTargetIsAhead() {
        when(mapper.selectCandidates(7L, MONDAY, FRIDAY)).thenReturn(List.of(
                candidate(1L, "A", 3, 5, 12),
                candidate(2L, "B", 6, 6, 6)));
        List<CollectionProgressItemVO> result = calculator.calculate(7L, MONDAY, FRIDAY);
        assertThat(result).extracting(CollectionProgressItemVO::getSubjectId).containsExactly(1L);
    }

    @Test
    void marksCompletionWithoutChangingCollectionType() {
        when(mapper.selectCandidates(7L, MONDAY, FRIDAY))
                .thenReturn(List.of(candidate(2L, "B", 5, 6, 6)));
        assertThat(calculator.calculate(7L, MONDAY, FRIDAY).getFirst())
                .extracting(CollectionProgressItemVO::isCompletedAfterUpdate,
                        CollectionProgressItemVO::isSuggestMarkAsWatched)
                .containsExactly(true, true);
    }

    @Test
    void returnsEmptyWhenCutoffBeforeWeekStart() {
        assertThat(calculator.calculate(7L, MONDAY, MONDAY.minusDays(1))).isEmpty();
        verify(mapper, never()).selectCandidates(any(), any(), any());
    }

    private static CollectionProgressCandidate candidate(Long subjectId, String name,
                                                         Integer current, Integer target, Integer total) {
        return CollectionProgressCandidate.builder()
                .subjectId(subjectId)
                .subjectName(name)
                .currentEpStatus(current)
                .targetEpStatus(target)
                .totalEpisodes(total)
                .build();
    }
}
