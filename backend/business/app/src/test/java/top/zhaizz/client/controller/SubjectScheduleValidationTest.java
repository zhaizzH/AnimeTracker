package top.zhaizz.client.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import top.zhaizz.app.AppApplication;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** /schedule 非法季度参数应返回 400（与 /season 对齐），而非 500 */
@SpringBootTest(classes = AppApplication.class)
@AutoConfigureMockMvc
@ActiveProfiles("local")
class SubjectScheduleValidationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void invalidQuarterReturns400() throws Exception {
        mockMvc.perform(get("/api/client/subjects/schedule")
                        .param("year", "2026")
                        .param("quarter", "invalid"))
                .andExpect(status().isBadRequest());
    }

    /** /season 缺 quarter 参数应返回 400（SeasonQueryDTO.quarter @NotBlank 兜底，覆盖折叠后缺参不再静默透传） */
    @Test
    void missingQuarterReturns400() throws Exception {
        mockMvc.perform(get("/api/client/subjects/season")
                        .param("year", "2026"))
                .andExpect(status().isBadRequest());
    }
}
