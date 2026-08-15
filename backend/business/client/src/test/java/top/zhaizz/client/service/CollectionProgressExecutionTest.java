package top.zhaizz.client.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.client.model.ProgressPreviewSnapshot;
import top.zhaizz.client.model.ProgressPreviewStatus;
import top.zhaizz.client.service.impl.CollectionProgressServiceImpl;
import top.zhaizz.client.store.ProgressPreviewStore;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressFailureVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.time.Clock;
import java.time.Duration;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

/**
 * 收藏进度确认执行测试（重新校验、部分成功、幂等重放、404/409）
 */
@ExtendWith(MockitoExtension.class)
class CollectionProgressExecutionTest {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");
    private static final OffsetDateTime NOW = OffsetDateTime.parse("2026-08-15T12:00:00+08:00");
    private static final LocalDate WEEK_START = LocalDate.of(2026, 8, 10);
    private static final LocalDate CUTOFF = LocalDate.of(2026, 8, 14);

    @Mock
    private CollectionProgressCalculator calculator;
    @Mock
    private ProgressPreviewStore store;
    @Mock
    private CollectionProgressItemExecutor itemExecutor;

    private CollectionProgressServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new CollectionProgressServiceImpl(calculator, store, itemExecutor,
                Clock.fixed(NOW.toInstant(), SHANGHAI));
    }

    @Test
    void changedPreviewInvalidatesOldSnapshotReturnsNewPreviewAndWritesNothing() {
        when(store.find(7L, "p1")).thenReturn(Optional.of(snapshot(List.of(itemWithTarget(5)))));
        when(store.tryLock(7L, "p1")).thenReturn(true);
        when(calculator.calculate(7L, WEEK_START, CUTOFF)).thenReturn(List.of(itemWithTarget(6)));

        CollectionProgressExecutionVO result = service.executePreview(7L, "p1");

        assertThat(result.getState()).isEqualTo(CollectionProgressState.PREVIEW_CHANGED);
        assertThat(result.getPreview().getItems()).extracting(CollectionProgressItemVO::getTargetEpStatus)
                .containsExactly(6);
        verify(store).invalidate(7L, "p1");
        // 新预览以新 previewId 持久化（供二次确认），不触碰业务写入
        verify(store).save(any(ProgressPreviewSnapshot.class), eq(Duration.ofMinutes(10)));
        verify(store).unlock(7L, "p1");
        verifyNoInteractions(itemExecutor);
    }

    @Test
    void unchangedPreviewExecutesEveryItemAndStoresCompletedResult() {
        when(store.find(7L, "p1")).thenReturn(Optional.of(snapshot(List.of(itemWithTarget(5)))));
        when(store.tryLock(7L, "p1")).thenReturn(true);
        when(calculator.calculate(7L, WEEK_START, CUTOFF)).thenReturn(List.of(itemWithTarget(5)));

        CollectionProgressExecutionVO result = service.executePreview(7L, "p1");

        assertThat(result.getState()).isEqualTo(CollectionProgressState.COMPLETED);
        assertThat(result.isReplayed()).isFalse();
        assertThat(result.getSucceeded()).extracting(CollectionProgressItemVO::getSubjectId).containsExactly(1L);
        assertThat(result.getSkipped()).isEmpty();
        assertThat(result.getFailed()).isEmpty();

        verify(itemExecutor).update(7L, itemWithTarget(5));
        ArgumentCaptor<ProgressPreviewSnapshot> captor = ArgumentCaptor.forClass(ProgressPreviewSnapshot.class);
        verify(store).saveCompleted(captor.capture());
        assertThat(captor.getValue().getStatus()).isEqualTo(ProgressPreviewStatus.COMPLETED);
        assertThat(captor.getValue().getExecutionResult().getState()).isEqualTo(CollectionProgressState.COMPLETED);
        verify(store).unlock(7L, "p1");
    }

    @Test
    void partialFailureAggregatesSkippedAndFailedButLaterItemsSucceed() {
        List<CollectionProgressItemVO> items = List.of(
                item(1L, 3, 5), item(2L, 4, 6), item(3L, 5, 7));
        when(store.find(7L, "p1")).thenReturn(Optional.of(snapshot(items)));
        when(store.tryLock(7L, "p1")).thenReturn(true);
        when(calculator.calculate(7L, WEEK_START, CUTOFF)).thenReturn(items);
        doThrow(new BizException(ErrorType.CONFLICT, "收藏进度已发生变化"))
                .when(itemExecutor).update(7L, item(1L, 3, 5));
        doThrow(new RuntimeException("数据库连接失败"))
                .when(itemExecutor).update(7L, item(2L, 4, 6));

        CollectionProgressExecutionVO result = service.executePreview(7L, "p1");

        assertThat(result.getState()).isEqualTo(CollectionProgressState.COMPLETED);
        assertThat(result.getSucceeded()).extracting(CollectionProgressItemVO::getSubjectId).containsExactly(3L);
        assertThat(result.getSkipped()).extracting(CollectionProgressFailureVO::getSubjectId).containsExactly(1L);
        assertThat(result.getSkipped().getFirst().getReason()).isEqualTo("收藏进度已发生变化");
        assertThat(result.getFailed()).extracting(CollectionProgressFailureVO::getSubjectId).containsExactly(2L);
        assertThat(result.getFailed().getFirst().getReason()).isEqualTo("数据库连接失败");
        verify(itemExecutor).update(7L, item(3L, 5, 7));
        verify(store).unlock(7L, "p1");
    }

    @Test
    void completedSnapshotReturnsStoredResultWithReplayedFlag() {
        CollectionProgressExecutionVO stored = CollectionProgressExecutionVO.builder()
                .state(CollectionProgressState.COMPLETED)
                .replayed(false)
                .succeeded(List.of(itemWithTarget(5)))
                .build();
        ProgressPreviewSnapshot snapshot = ProgressPreviewSnapshot.builder()
                .previewId("p1")
                .userId(7L)
                .status(ProgressPreviewStatus.COMPLETED)
                .weekStart(WEEK_START)
                .cutoffDate(CUTOFF)
                .items(List.of(itemWithTarget(5)))
                .createdAt(NOW)
                .expiresAt(NOW.plusMinutes(10))
                .executionResult(stored)
                .build();
        when(store.find(7L, "p1")).thenReturn(Optional.of(snapshot));
        when(store.tryLock(7L, "p1")).thenReturn(true);

        CollectionProgressExecutionVO result = service.executePreview(7L, "p1");

        assertThat(result.isReplayed()).isTrue();
        assertThat(result.getState()).isEqualTo(CollectionProgressState.COMPLETED);
        assertThat(result.getSucceeded()).extracting(CollectionProgressItemVO::getSubjectId).containsExactly(1L);
        verifyNoInteractions(itemExecutor);
        verify(store).unlock(7L, "p1");
    }

    @Test
    void missingPreviewThrowsNotFound() {
        when(store.find(7L, "p1")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.executePreview(7L, "p1"))
                .isInstanceOfSatisfying(BizException.class, e -> assertThat(e.getCode()).isEqualTo(404));
        verify(store, never()).tryLock(any(), any());
        verify(store, never()).unlock(any(), any());
    }

    @Test
    void lockedPreviewThrowsConflictWithoutUnlock() {
        when(store.find(7L, "p1")).thenReturn(Optional.of(snapshot(List.of(itemWithTarget(5)))));
        when(store.tryLock(7L, "p1")).thenReturn(false);

        assertThatThrownBy(() -> service.executePreview(7L, "p1"))
                .isInstanceOfSatisfying(BizException.class, e -> assertThat(e.getCode()).isEqualTo(409));
        verify(store, never()).unlock(7L, "p1");
    }

    @Test
    void invalidatedSnapshotThrowsConflictAndReleasesLock() {
        when(store.find(7L, "p1"))
                .thenReturn(Optional.of(snapshot(ProgressPreviewStatus.INVALIDATED, List.of(itemWithTarget(5)))));
        when(store.tryLock(7L, "p1")).thenReturn(true);

        assertThatThrownBy(() -> service.executePreview(7L, "p1"))
                .isInstanceOfSatisfying(BizException.class, e -> assertThat(e.getCode()).isEqualTo(409));
        verify(store).unlock(7L, "p1");
    }

    @Test
    void expiredSnapshotThrowsConflictAndReleasesLock() {
        when(store.find(7L, "p1"))
                .thenReturn(Optional.of(snapshot(ProgressPreviewStatus.PENDING, List.of(itemWithTarget(5)), NOW.minusMinutes(1))));
        when(store.tryLock(7L, "p1")).thenReturn(true);

        assertThatThrownBy(() -> service.executePreview(7L, "p1"))
                .isInstanceOfSatisfying(BizException.class, e -> assertThat(e.getCode()).isEqualTo(409));
        verify(store).unlock(7L, "p1");
    }

    private static ProgressPreviewSnapshot snapshot(List<CollectionProgressItemVO> items) {
        return snapshot(ProgressPreviewStatus.PENDING, items, NOW.plusMinutes(10));
    }

    private static ProgressPreviewSnapshot snapshot(ProgressPreviewStatus status, List<CollectionProgressItemVO> items) {
        return snapshot(status, items, NOW.plusMinutes(10));
    }

    private static ProgressPreviewSnapshot snapshot(ProgressPreviewStatus status, List<CollectionProgressItemVO> items,
                                                    OffsetDateTime expiresAt) {
        return ProgressPreviewSnapshot.builder()
                .previewId("p1")
                .userId(7L)
                .status(status)
                .weekStart(WEEK_START)
                .cutoffDate(CUTOFF)
                .items(items)
                .createdAt(NOW)
                .expiresAt(expiresAt)
                .build();
    }

    private static CollectionProgressItemVO itemWithTarget(Integer target) {
        return item(1L, 5, target);
    }

    private static CollectionProgressItemVO item(Long subjectId, Integer current, Integer target) {
        return CollectionProgressItemVO.builder()
                .subjectId(subjectId)
                .subjectName("S" + subjectId)
                .currentEpStatus(current)
                .targetEpStatus(target)
                .build();
    }
}
