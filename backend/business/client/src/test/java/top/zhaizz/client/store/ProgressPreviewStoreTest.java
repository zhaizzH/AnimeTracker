package top.zhaizz.client.store;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.client.model.ProgressPreviewSnapshot;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.util.RedisUtil;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 收藏进度 Redis 快照与执行锁存储测试
 */
@ExtendWith(MockitoExtension.class)
class ProgressPreviewStoreTest {

    @Mock
    private RedisUtil redis;

    @Mock
    private ObjectMapper objectMapper;

    private ProgressPreviewStore store;

    @BeforeEach
    void setUp() {
        store = new ProgressPreviewStore(redis, objectMapper);
    }

    @Test
    void keyIncludesUserAndPreviewId() throws Exception {
        when(objectMapper.writeValueAsString(any(ProgressPreviewSnapshot.class))).thenReturn("{}");
        store.save(snapshot(9L, "p1"), Duration.ofMinutes(10));
        verify(redis).set(eq("collection:progress-preview:9:p1"), anyString(), eq(10L), eq(TimeUnit.MINUTES));
    }

    @Test
    void lockUsesSetIfAbsentAndThirtySecondTtl() {
        when(redis.setIfAbsent(anyString(), anyString(), anyLong(), any())).thenReturn(true);
        assertThat(store.tryLock(9L, "p1")).isTrue();
        verify(redis).setIfAbsent(eq("collection:progress-lock:9:p1"), anyString(), eq(30L), eq(TimeUnit.SECONDS));
    }

    @Test
    void corruptedSnapshotRaisesInternalError() throws Exception {
        when(redis.get("collection:progress-preview:9:p1")).thenReturn("not-json");
        when(objectMapper.readValue("not-json", ProgressPreviewSnapshot.class))
                .thenThrow(new JsonProcessingException("bad snapshot") {});

        assertThatThrownBy(() -> store.find(9L, "p1"))
                .isInstanceOfSatisfying(BizException.class,
                        e -> assertThat(e.getCode()).isEqualTo(500));
    }

    private static ProgressPreviewSnapshot snapshot(Long userId, String previewId) {
        return ProgressPreviewSnapshot.builder()
                .userId(userId)
                .previewId(previewId)
                .build();
    }
}
