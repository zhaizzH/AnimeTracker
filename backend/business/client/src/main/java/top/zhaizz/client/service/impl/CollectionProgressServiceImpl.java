package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.model.ProgressPreviewSnapshot;
import top.zhaizz.client.model.ProgressPreviewStatus;
import top.zhaizz.client.service.CollectionProgressCalculator;
import top.zhaizz.client.service.CollectionProgressItemExecutor;
import top.zhaizz.client.service.CollectionProgressService;
import top.zhaizz.client.store.ProgressPreviewStore;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressFailureVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.time.Clock;
import java.time.DayOfWeek;
import java.time.Duration;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * 收藏进度预览服务实现
 */
@Service
@RequiredArgsConstructor
public class CollectionProgressServiceImpl implements CollectionProgressService {

    private static final Duration PREVIEW_TTL = Duration.ofMinutes(10);

    private final CollectionProgressCalculator calculator;
    private final ProgressPreviewStore store;
    private final CollectionProgressItemExecutor itemExecutor;
    private final Clock clock;

    @Override
    public CollectionProgressPreviewVO createPreview(Long userId) {
        LocalDate today = LocalDate.now(clock);
        LocalDate weekStart = today.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        LocalDate cutoffDate = today.minusDays(1);

        List<CollectionProgressItemVO> items = calculator.calculate(userId, weekStart, cutoffDate);

        String previewId = UUID.randomUUID().toString();
        OffsetDateTime now = OffsetDateTime.now(clock);
        OffsetDateTime expiresAt = now.plus(PREVIEW_TTL);

        ProgressPreviewSnapshot snapshot = ProgressPreviewSnapshot.builder()
                .previewId(previewId)
                .userId(userId)
                .status(ProgressPreviewStatus.PENDING)
                .weekStart(weekStart)
                .cutoffDate(cutoffDate)
                .items(items)
                .createdAt(now)
                .expiresAt(expiresAt)
                .build();
        store.save(snapshot, PREVIEW_TTL);

        return toPreviewVO(CollectionProgressState.PENDING, previewId, items, weekStart, cutoffDate, expiresAt);
    }

    @Override
    public CollectionProgressExecutionVO executePreview(Long userId, String previewId) {
        ProgressPreviewSnapshot snapshot = store.find(userId, previewId)
                .orElseThrow(() -> new BizException(ErrorType.NOT_FOUND, "预览不存在"));

        // 未取得执行锁（30 秒 SET NX）视为正在执行，未持锁不释放
        if (!store.tryLock(userId, previewId)) {
            throw new BizException(ErrorType.CONFLICT, "预览正在执行中，请稍后重试");
        }
        try {
            return executeLocked(userId, previewId, snapshot);
        } finally {
            store.unlock(userId, previewId);
        }
    }

    private CollectionProgressExecutionVO executeLocked(Long userId, String previewId,
                                                       ProgressPreviewSnapshot snapshot) {
        // 幂等重放：已完成的预览直接返回首次执行结果
        if (snapshot.getStatus() == ProgressPreviewStatus.COMPLETED && snapshot.getExecutionResult() != null) {
            CollectionProgressExecutionVO replayed = snapshot.getExecutionResult();
            replayed.setReplayed(true);
            return replayed;
        }
        // 非 PENDING（执行中/失败/已失效）或已过期 → 409
        if (snapshot.getStatus() != ProgressPreviewStatus.PENDING) {
            throw new BizException(ErrorType.CONFLICT, "预览状态已变化，请重新生成");
        }
        if (snapshot.getExpiresAt() != null && snapshot.getExpiresAt().isBefore(OffsetDateTime.now(clock))) {
            throw new BizException(ErrorType.CONFLICT, "预览已过期，请重新生成");
        }

        // 重新计算并对比原快照；任何变化 → 旧预览失效、返回新预览，不执行写入
        List<CollectionProgressItemVO> recalculated = calculator.calculate(userId, snapshot.getWeekStart(), snapshot.getCutoffDate());
        if (!sameItems(snapshot.getItems(), recalculated)) {
            store.invalidate(userId, previewId);
            String newPreviewId = UUID.randomUUID().toString();
            OffsetDateTime now = OffsetDateTime.now(clock);
            OffsetDateTime newExpiresAt = now.plus(PREVIEW_TTL);
            store.save(ProgressPreviewSnapshot.builder()
                    .previewId(newPreviewId)
                    .userId(userId)
                    .status(ProgressPreviewStatus.PENDING)
                    .weekStart(snapshot.getWeekStart())
                    .cutoffDate(snapshot.getCutoffDate())
                    .items(recalculated)
                    .createdAt(now)
                    .expiresAt(newExpiresAt)
                    .build(), PREVIEW_TTL);
            return CollectionProgressExecutionVO.builder()
                    .state(CollectionProgressState.PREVIEW_CHANGED)
                    .replayed(false)
                    .preview(toPreviewVO(CollectionProgressState.PREVIEW_CHANGED, newPreviewId,
                            recalculated, snapshot.getWeekStart(), snapshot.getCutoffDate(), newExpiresAt))
                    .build();
        }

        // 完全一致 → 状态置 EXECUTING 并持久化，逐项独立事务执行，允许部分成功
        snapshot.setStatus(ProgressPreviewStatus.EXECUTING);
        store.save(snapshot, PREVIEW_TTL);

        List<CollectionProgressItemVO> succeeded = new ArrayList<>();
        List<CollectionProgressFailureVO> skipped = new ArrayList<>();
        List<CollectionProgressFailureVO> failed = new ArrayList<>();
        for (CollectionProgressItemVO item : recalculated) {
            try {
                itemExecutor.update(userId, item);
                succeeded.add(item);
            } catch (BizException e) {
                skipped.add(toFailure(item, e.getMessage()));
            } catch (RuntimeException e) {
                failed.add(toFailure(item, e.getMessage()));
            }
        }

        CollectionProgressExecutionVO result = CollectionProgressExecutionVO.builder()
                .state(CollectionProgressState.COMPLETED)
                .replayed(false)
                .succeeded(succeeded)
                .skipped(skipped)
                .failed(failed)
                .build();

        // 结果以 COMPLETED 快照保存 10 分钟，供重复确认幂等返回
        ProgressPreviewSnapshot completed = ProgressPreviewSnapshot.builder()
                .previewId(previewId)
                .userId(userId)
                .status(ProgressPreviewStatus.COMPLETED)
                .weekStart(snapshot.getWeekStart())
                .cutoffDate(snapshot.getCutoffDate())
                .items(snapshot.getItems())
                .createdAt(snapshot.getCreatedAt())
                .expiresAt(OffsetDateTime.now(clock).plus(PREVIEW_TTL))
                .executionResult(result)
                .build();
        store.saveCompleted(completed);

        return result;
    }

    /** 规范化三元组 (subjectId, currentEpStatus, targetEpStatus) 按 subjectId 确定性排序后比较 */
    private boolean sameItems(List<CollectionProgressItemVO> original, List<CollectionProgressItemVO> recalculated) {
        return normalize(original).equals(normalize(recalculated));
    }

    private List<List<Object>> normalize(List<CollectionProgressItemVO> items) {
        return items.stream()
                .sorted(Comparator.comparing(CollectionProgressItemVO::getSubjectId,
                        Comparator.nullsLast(Comparator.naturalOrder())))
                .map(i -> List.<Object>of(i.getSubjectId(), i.getCurrentEpStatus(), i.getTargetEpStatus()))
                .toList();
    }

    private CollectionProgressFailureVO toFailure(CollectionProgressItemVO item, String reason) {
        return CollectionProgressFailureVO.builder()
                .subjectId(item.getSubjectId())
                .subjectName(item.getSubjectName())
                .currentEpStatus(item.getCurrentEpStatus())
                .targetEpStatus(item.getTargetEpStatus())
                .reason(reason)
                .build();
    }

    /** 构造预览返回体（createPreview 与确认时 PREVIEW_CHANGED 共用） */
    private CollectionProgressPreviewVO toPreviewVO(CollectionProgressState state, String previewId,
                                                    List<CollectionProgressItemVO> items,
                                                    LocalDate weekStart, LocalDate cutoffDate,
                                                    OffsetDateTime expiresAt) {
        return CollectionProgressPreviewVO.builder()
                .previewId(previewId)
                .state(state)
                .expiresAt(expiresAt)
                .weekStart(weekStart)
                .cutoffDate(cutoffDate)
                .items(items)
                .build();
    }
}
