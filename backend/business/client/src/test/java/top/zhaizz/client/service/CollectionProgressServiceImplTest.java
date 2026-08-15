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
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 收藏进度预览生成测试（日期边界 + Redis 快照写入）
 */
@ExtendWith(MockitoExtension.class)
class CollectionProgressServiceImplTest {

    private static final ZoneId SHANGHAI = ZoneId.of("Asia/Shanghai");

    @Mock
    private CollectionProgressCalculator calculator;
    @Mock
    private ProgressPreviewStore store;

    private Clock clock;
    private CollectionProgressServiceImpl service;

    @BeforeEach
    void setUp() {
        clock = Clock.fixed(Instant.parse("2026-08-15T04:00:00Z"), SHANGHAI);
        service = new CollectionProgressServiceImpl(calculator, store, clock);
    }

    @Test
    void createPreviewComputesWeekRangeAndPersistsSnapshot() {
        when(calculator.calculate(7L, LocalDate.of(2026, 8, 10), LocalDate.of(2026, 8, 14)))
                .thenReturn(List.of());

        CollectionProgressPreviewVO preview = service.createPreview(7L);

        assertThat(preview.getWeekStart()).isEqualTo(LocalDate.of(2026, 8, 10));
        assertThat(preview.getCutoffDate()).isEqualTo(LocalDate.of(2026, 8, 14));
        assertThat(preview.getState()).isEqualTo(CollectionProgressState.PENDING);
        // previewId 为合法 UUID
        assertThat(UUID.fromString(preview.getPreviewId())).isNotNull();

        ArgumentCaptor<ProgressPreviewSnapshot> captor = ArgumentCaptor.forClass(ProgressPreviewSnapshot.class);
        verify(store, times(1)).save(captor.capture(), eq(Duration.ofMinutes(10)));
        ProgressPreviewSnapshot saved = captor.getValue();
        assertThat(saved.getUserId()).isEqualTo(7L);
        assertThat(saved.getPreviewId()).isEqualTo(preview.getPreviewId());
        assertThat(saved.getWeekStart()).isEqualTo(LocalDate.of(2026, 8, 10));
        assertThat(saved.getCutoffDate()).isEqualTo(LocalDate.of(2026, 8, 14));
        assertThat(saved.getStatus()).isEqualTo(ProgressPreviewStatus.PENDING);
        // 10 分钟过期
        assertThat(saved.getExpiresAt()).isEqualTo(saved.getCreatedAt().plusMinutes(10));
    }

    @Test
    void createPreviewOnMondayPassesCutoffBeforeWeekStartAndProducesEmptyPreview() {
        // 2026-08-16T16:00:00Z = 2026-08-17T00:00+08:00（周一）
        clock = Clock.fixed(Instant.parse("2026-08-16T16:00:00Z"), SHANGHAI);
        service = new CollectionProgressServiceImpl(calculator, store, clock);
        when(calculator.calculate(7L, LocalDate.of(2026, 8, 17), LocalDate.of(2026, 8, 16)))
                .thenReturn(List.of());

        CollectionProgressPreviewVO preview = service.createPreview(7L);

        assertThat(preview.getItems()).isEmpty();
        verify(calculator).calculate(7L, LocalDate.of(2026, 8, 17), LocalDate.of(2026, 8, 16));
    }
}
