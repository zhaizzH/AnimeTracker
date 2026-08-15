package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.model.ProgressPreviewSnapshot;
import top.zhaizz.client.model.ProgressPreviewStatus;
import top.zhaizz.client.service.CollectionProgressCalculator;
import top.zhaizz.client.service.CollectionProgressService;
import top.zhaizz.client.store.ProgressPreviewStore;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.time.Clock;
import java.time.DayOfWeek;
import java.time.Duration;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.temporal.TemporalAdjusters;
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
