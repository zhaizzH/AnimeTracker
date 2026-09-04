package top.zhaizz.client.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import top.zhaizz.client.service.EvidenceService;
import top.zhaizz.pojo.dto.evidence.EvidenceEntityBatchRequestDTO;
import top.zhaizz.pojo.dto.evidence.EvidenceEntityType;
import top.zhaizz.pojo.vo.evidence.EvidenceCandidateVO;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class EvidenceControllerTest {

    private MockMvc mvc;
    private EvidenceService evidenceService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @BeforeEach
    void setUp() {
        evidenceService = mock(EvidenceService.class);
        EvidenceController controller = new EvidenceController(evidenceService);
        mvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    void batchEvidenceReturnsCandidates() throws Exception {
        EvidenceCandidateVO vo = EvidenceCandidateVO.builder()
                .subjectId(1L)
                .name("Test")
                .nameCn("测试")
                .type(2)
                .nsfw(false)
                .score(new BigDecimal("7.5"))
                .ratingTotal(100)
                .collectionTotal(500)
                .airDate(LocalDate.of(2024, 1, 1))
                .sourceTime(LocalDateTime.of(2026, 8, 1, 12, 0))
                .aliases(List.of("テスト"))
                .metaTags(List.of("SF"))
                .build();

        when(evidenceService.batchEvidence(List.of(1L))).thenReturn(List.of(vo));

        mvc.perform(post("/api/client/evidence/batch")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"subjectIds\":[1]}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].subjectId").value(1))
                .andExpect(jsonPath("$.data[0].name").value("Test"))
                .andExpect(jsonPath("$.data[0].aliases[0]").value("テスト"))
                .andExpect(jsonPath("$.data[0].metaTags[0]").value("SF"));
    }

    @Test
    void batchEvidenceReturnsEmptyForMissingIds() throws Exception {
        when(evidenceService.batchEvidence(anyList())).thenReturn(Collections.emptyList());

        mvc.perform(post("/api/client/evidence/batch")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"subjectIds\":[999]}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").isEmpty());
    }

    @Test
    void batchEvidenceRejectsEmptyIds() throws Exception {
        mvc.perform(post("/api/client/evidence/batch")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"subjectIds\":[]}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void batchEvidenceRejectsTooManyIds() throws Exception {
        List<Long> ids = new java.util.ArrayList<>();
        for (long i = 1; i <= 51; i++) ids.add(i);

        mvc.perform(post("/api/client/evidence/batch")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of("subjectIds", ids))))
                .andExpect(status().isBadRequest());
    }

    @Test
    void batchEvidenceRejectsNullIds() throws Exception {
        mvc.perform(post("/api/client/evidence/batch")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void resolveEvidenceReturnsSafeCandidateForPerson() throws Exception {
        EvidenceCandidateVO vo = EvidenceCandidateVO.builder()
                .subjectId(11L)
                .name("Person work")
                .type(2)
                .nsfw(false)
                .active(true)
                .sourceId(101)
                .sourceUrl("https://bgm.tv/subject/101")
                .build();
        when(evidenceService.resolveEvidence(any(EvidenceEntityBatchRequestDTO.class)))
                .thenReturn(List.of(vo));

        mvc.perform(post("/api/client/evidence/resolve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"entityType\":\"PERSON\",\"ids\":[7]}") )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data[0].subjectId").value(11))
                .andExpect(jsonPath("$.data[0].type").value(2))
                .andExpect(jsonPath("$.data[0].nsfw").value(false))
                .andExpect(jsonPath("$.data[0].active").value(true))
                .andExpect(jsonPath("$.data[0].sourceId").value(101))
                .andExpect(jsonPath("$.data[0].sourceUrl").value("https://bgm.tv/subject/101"));
    }

    @Test
    void resolveEvidenceReturnsEmptyForUnknownEntity() throws Exception {
        when(evidenceService.resolveEvidence(any(EvidenceEntityBatchRequestDTO.class)))
                .thenReturn(Collections.emptyList());

        mvc.perform(post("/api/client/evidence/resolve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"entityType\":\"CHARACTER\",\"ids\":[999]}") )
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data").isEmpty());
    }

    @Test
    void resolveEvidenceRejectsInvalidIdsAndMissingType() throws Exception {
        mvc.perform(post("/api/client/evidence/resolve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"entityType\":\"ACTOR\",\"ids\":[0]}") )
                .andExpect(status().isBadRequest());

        mvc.perform(post("/api/client/evidence/resolve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"ids\":[1]}") )
                .andExpect(status().isBadRequest());
    }

    @Test
    void resolveEvidenceRejectsMoreThanFiftyIds() throws Exception {
        List<Long> ids = java.util.stream.LongStream.rangeClosed(1, 51).boxed().toList();

        mvc.perform(post("/api/client/evidence/resolve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of(
                                "entityType", EvidenceEntityType.SUBJECT,
                                "ids", ids))))
                .andExpect(status().isBadRequest());
    }
}
