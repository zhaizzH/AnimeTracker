package top.zhaizz.client.contract;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import top.zhaizz.client.controller.SubjectController;
import top.zhaizz.client.service.ClientSubjectService;
import top.zhaizz.client.service.EpisodeService;
import top.zhaizz.pojo.vo.subject.SubjectBatchResultVO;

import java.util.List;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** 批量回查 HTTP 契约：参数校验、匿名与可选登录态。 */
class SubjectBatchContractTest {

    private ClientSubjectService subjectService;
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        subjectService = mock(ClientSubjectService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(new SubjectController(subjectService, mock(EpisodeService.class))).build();
    }

    @AfterEach
    void tearDown() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void rejectsMoreThanOneHundredIds() throws Exception {
        String ids = java.util.stream.LongStream.rangeClosed(1, 101)
                .mapToObj(String::valueOf)
                .collect(java.util.stream.Collectors.joining(","));

        mockMvc.perform(post("/api/client/subjects/batch")
                        .contentType("application/json")
                        .content("{\"subjectIds\":[" + ids + "],\"excludeCollected\":true}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void anonymousRequestIsAllowedAndDoesNotApplyCollectionFilter() throws Exception {
        when(subjectService.batch(List.of(8L, 2L), true, null)).thenReturn(new SubjectBatchResultVO());

        mockMvc.perform(post("/api/client/subjects/batch")
                        .contentType("application/json")
                        .content("{\"subjectIds\":[8,2],\"excludeCollected\":true}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        verify(subjectService).batch(List.of(8L, 2L), true, null);
    }

    @Test
    void authenticatedRequestUsesQuietCurrentUser() throws Exception {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                7L, null, List.of(new SimpleGrantedAuthority("ROLE_USER"))));
        when(subjectService.batch(List.of(8L, 2L, 8L), true, 7L)).thenReturn(new SubjectBatchResultVO());

        mockMvc.perform(post("/api/client/subjects/batch")
                        .contentType("application/json")
                        .content("{\"subjectIds\":[8,2,8],\"excludeCollected\":true}"))
                .andExpect(status().isOk());

        verify(subjectService).batch(eq(List.of(8L, 2L, 8L)), eq(true), eq(7L));
    }
}
