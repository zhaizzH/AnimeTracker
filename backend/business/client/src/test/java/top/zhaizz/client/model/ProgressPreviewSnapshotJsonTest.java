package top.zhaizz.client.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.Test;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 特征化 {@code ProgressPreviewSnapshot} 迁移后的 Jackson 往返契约
 *
 * <p>该快照由 {@code ProgressPreviewStore} 序列化后写入 Redis 并读回，因此迁移前后
 * 属性名、可空字段与 {@code @Builder.Default} 列表字段的读写必须保持一致
 */
class ProgressPreviewSnapshotJsonTest {

    /** 快照序列化使用与运行时一致的 Jackson 时间模块 */
    private static final ObjectMapper MAPPER = JsonMapper.builder().addModule(new JavaTimeModule()).build();

    /**
     * 验证 Jackson 往返后全部属性取回一致，包括时间与嵌套条目列表
     * @throws Exception 序列化或反序列化失败
     */
    @Test
    void roundTripsThroughJackson() throws Exception {
        CollectionProgressItemVO item = CollectionProgressItemVO.builder()
                .subjectId(42L)
                .subjectName("示例条目")
                .currentEpStatus(5)
                .targetEpStatus(6)
                .build();
        OffsetDateTime createdAt = OffsetDateTime.parse("2026-09-28T10:00:00+08:00");
        OffsetDateTime expiresAt = createdAt.plusMinutes(10);
        ProgressPreviewSnapshot snapshot = ProgressPreviewSnapshot.builder()
                .previewId("preview-1")
                .userId(99L)
                .status(ProgressPreviewStatus.PENDING)
                .weekStart(LocalDate.of(2026, 9, 21))
                .cutoffDate(LocalDate.of(2026, 9, 27))
                .items(List.of(item))
                .createdAt(createdAt)
                .expiresAt(expiresAt)
                .build();

        String json = MAPPER.writeValueAsString(snapshot);
        ProgressPreviewSnapshot restored = MAPPER.readValue(json, ProgressPreviewSnapshot.class);

        assertThat(restored.getPreviewId()).isEqualTo("preview-1");
        assertThat(restored.getUserId()).isEqualTo(99L);
        assertThat(restored.getStatus()).isEqualTo(ProgressPreviewStatus.PENDING);
        assertThat(restored.getWeekStart()).isEqualTo(LocalDate.of(2026, 9, 21));
        assertThat(restored.getCutoffDate()).isEqualTo(LocalDate.of(2026, 9, 27));
        assertThat(restored.getCreatedAt()).isEqualTo(createdAt);
        assertThat(restored.getExpiresAt()).isEqualTo(expiresAt);
        assertThat(restored.getItems()).hasSize(1);
        assertThat(restored.getItems().get(0).getSubjectId()).isEqualTo(42L);
        assertThat(restored.getItems().get(0).getSubjectName()).isEqualTo("示例条目");
        assertThat(restored.getItems().get(0).getCurrentEpStatus()).isEqualTo(5);
        assertThat(restored.getItems().get(0).getTargetEpStatus()).isEqualTo(6);
    }

    /**
     * 验证未提供条目列表的构建结果序列化后仍可读回，默认空列表不产生空指针
     * @throws Exception 序列化或反序列化失败
     */
    @Test
    void roundTripsDefaultEmptyItems() throws Exception {
        ProgressPreviewSnapshot snapshot = ProgressPreviewSnapshot.builder()
                .previewId("preview-2")
                .userId(1L)
                .build();

        String json = MAPPER.writeValueAsString(snapshot);
        ProgressPreviewSnapshot restored = MAPPER.readValue(json, ProgressPreviewSnapshot.class);

        assertThat(restored.getItems()).isNotNull();
        assertThat(restored.getItems()).isEmpty();
    }

    /**
     * 验证执行结果字段随快照往返，完成后幂等重放可还原执行结果
     * @throws Exception 序列化或反序列化失败
     */
    @Test
    void roundTripsExecutionResult() throws Exception {
        var execution = top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO.builder()
                .state(CollectionProgressState.COMPLETED)
                .replayed(true)
                .build();
        ProgressPreviewSnapshot snapshot = ProgressPreviewSnapshot.builder()
                .previewId("preview-3")
                .userId(5L)
                .status(ProgressPreviewStatus.COMPLETED)
                .executionResult(execution)
                .build();

        String json = MAPPER.writeValueAsString(snapshot);
        ProgressPreviewSnapshot restored = MAPPER.readValue(json, ProgressPreviewSnapshot.class);

        assertThat(restored.getExecutionResult()).isNotNull();
        assertThat(restored.getExecutionResult().getState()).isEqualTo(CollectionProgressState.COMPLETED);
        assertThat(restored.getExecutionResult().isReplayed()).isTrue();
    }
}
