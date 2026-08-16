package top.zhaizz.app;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.web.servlet.MockMvc;
import top.zhaizz.client.service.CollectionProgressService;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressState;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;

import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.authentication;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 收藏进度预览接口 Result<T> 包装测试（MockMvc 全上下文，mock 掉服务层避免依赖 DB/Redis）
 */
@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:testdb;MODE=MySQL;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.flyway.enabled=false",
})
@AutoConfigureMockMvc
class CollectionProgressControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private CollectionProgressService collectionProgressService;

    @Test
    void createPreviewWrapsResultWithoutNestedCode() throws Exception {
        when(collectionProgressService.createPreview(7L)).thenReturn(preview());

        mockMvc.perform(post("/api/client/collections/progress-preview")
                        .with(authentication(authenticationFor(7L))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.message").value("success"))
                .andExpect(jsonPath("$.data.state").value("PENDING"))
                .andExpect(jsonPath("$.data.code").doesNotExist());
    }

    @Test
    void executePreviewWrapsResultWithoutNestedCode() throws Exception {
        when(collectionProgressService.executePreview(7L, "p1")).thenReturn(execution());

        mockMvc.perform(post("/api/client/collections/progress-preview/p1/execute")
                        .with(authentication(authenticationFor(7L))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.message").value("success"))
                .andExpect(jsonPath("$.data.state").value("COMPLETED"))
                .andExpect(jsonPath("$.data.replayed").value(false))
                .andExpect(jsonPath("$.data.code").doesNotExist());
    }

    @Test
    void executePreviewMissingPreviewMapsTo404ResultError() throws Exception {
        doThrow(new BizException(ErrorType.NOT_FOUND, "预览不存在"))
                .when(collectionProgressService).executePreview(7L, "p1");

        mockMvc.perform(post("/api/client/collections/progress-preview/p1/execute")
                        .with(authentication(authenticationFor(7L))))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value(404))
                .andExpect(jsonPath("$.message").value("预览不存在"));
    }

    @Test
    void executePreviewLockedMapsTo409ResultError() throws Exception {
        doThrow(new BizException(ErrorType.CONFLICT, "预览正在执行中，请稍后重试"))
                .when(collectionProgressService).executePreview(7L, "p1");

        mockMvc.perform(post("/api/client/collections/progress-preview/p1/execute")
                        .with(authentication(authenticationFor(7L))))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value(409))
                .andExpect(jsonPath("$.message").value("预览正在执行中，请稍后重试"));
    }

    private static Authentication authenticationFor(Long userId) {
        return new UsernamePasswordAuthenticationToken(userId, null,
                List.of(new SimpleGrantedAuthority("ROLE_USER")));
    }

    private static CollectionProgressPreviewVO preview() {
        return CollectionProgressPreviewVO.builder()
                .previewId("p1")
                .state(CollectionProgressState.PENDING)
                .expiresAt(OffsetDateTime.now())
                .weekStart(LocalDate.of(2026, 8, 10))
                .cutoffDate(LocalDate.of(2026, 8, 14))
                .items(List.of())
                .build();
    }

    private static CollectionProgressExecutionVO execution() {
        return CollectionProgressExecutionVO.builder()
                .state(CollectionProgressState.COMPLETED)
                .replayed(false)
                .succeeded(List.of())
                .skipped(List.of())
                .failed(List.of())
                .build();
    }
}
