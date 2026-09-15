package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.model.ProgressPreviewSnapshot;
import top.zhaizz.client.model.ProgressPreviewStatus;
import top.zhaizz.client.service.CollectionProgressCalculator;
import top.zhaizz.client.service.CollectionProgressItemExecutor;
import top.zhaizz.client.service.CollectionProgressService;
import top.zhaizz.client.converter.CollectionProgressConverter;
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

    /** 收藏进度预览快照的有效期 */
    private static final Duration PREVIEW_TTL = Duration.ofMinutes(10);

    /** 收藏进度计算器 */
    private final CollectionProgressCalculator calculator;
    /** 收藏进度快照存储 */
    private final ProgressPreviewStore store;
    /** 单条收藏进度执行器 */
    private final CollectionProgressItemExecutor itemExecutor;
    /** 用于计算时间的时钟，便于测试 */
    private final Clock clock;

    /** {@inheritDoc} */
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

        return CollectionProgressConverter.toPreviewVO(CollectionProgressState.PENDING, previewId, items, weekStart, cutoffDate, expiresAt);
    }

    /** {@inheritDoc} */
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

    /**
     * 在持有执行锁时重新校验并推进收藏，完成快照允许幂等重放
     * @param userId 快照所属用户 ID
     * @param previewId 已获取执行锁的预览标识
     * @param snapshot 保存的预览快照
     * @return 预览变化提示、逐项执行结果或首次结果的幂等重放
     * @throws BizException 非待执行状态或已过期时为 CONFLICT
     */
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
                    .preview(CollectionProgressConverter.toPreviewVO(CollectionProgressState.PREVIEW_CHANGED, newPreviewId,
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
                skipped.add(CollectionProgressConverter.toFailure(item, e.getMessage()));
            } catch (RuntimeException e) {
                failed.add(CollectionProgressConverter.toFailure(item, e.getMessage()));
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

    /**
     * 忽略顺序比较条目标识、当前进度和目标进度，不比较展示名称
     * @param original 原始预览条目列表
     * @param recalculated 重新计算的条目列表
     * @return 三元组规范化排序后相同为 {@code true}
     */
    private boolean sameItems(List<CollectionProgressItemVO> original, List<CollectionProgressItemVO> recalculated) {
        return normalize(original).equals(normalize(recalculated));
    }

    /**
     * 按稳定字段顺序提取进度条目，用于比较重算前后的内容是否一致
     *
     * @param items 进度条目集合
     * @return 可比较的字段列表；输入为空时返回空列表
     */
    private List<List<Object>> normalize(List<CollectionProgressItemVO> items) {
        return items.stream()
                .sorted(Comparator.comparing(CollectionProgressItemVO::getSubjectId,
                        Comparator.nullsLast(Comparator.naturalOrder())))
                .map(i -> List.<Object>of(i.getSubjectId(), i.getCurrentEpStatus(), i.getTargetEpStatus()))
                .toList();
    }

}
