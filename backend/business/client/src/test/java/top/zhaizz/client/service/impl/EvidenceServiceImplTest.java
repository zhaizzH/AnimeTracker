package top.zhaizz.client.service.impl;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.client.mapper.EvidenceMapper;
import top.zhaizz.client.model.*;
import top.zhaizz.pojo.dto.evidence.EvidenceEntityBatchRequestDTO;
import top.zhaizz.pojo.dto.evidence.EvidenceEntityType;
import top.zhaizz.pojo.vo.evidence.EvidenceCandidateVO;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.*;

/** 证据服务聚合、去重和安全筛选测试。 */
@ExtendWith(MockitoExtension.class)
class EvidenceServiceImplTest {

    /** 模拟证据查询结果。 */
    @Mock
    private EvidenceMapper evidenceMapper;

    /** 被测证据聚合服务。 */
    @InjectMocks
    private EvidenceServiceImpl evidenceService;

/** 空批量输入返回空结果。 */
    @Test
    void batchEvidenceReturnsEmptyForNullInput() {
        assertThat(evidenceService.batchEvidence(null)).isEmpty();
    }

/** 空 ID 集合返回空结果。 */
    @Test
    void batchEvidenceReturnsEmptyForEmptyInput() {
        assertThat(evidenceService.batchEvidence(Collections.emptyList())).isEmpty();
    }

/** 查询不到条目时返回空候选。 */
    @Test
    void batchEvidenceReturnsEmptyWhenNoSubjectsFound() {
        when(evidenceMapper.selectSubjectBasics(anyList())).thenReturn(Collections.emptyList());

        assertThat(evidenceService.batchEvidence(List.of(999L))).isEmpty();
    }

/** 聚合条目、别名、标签及主创关系为完整候选。 */
    @Test
    void batchEvidenceAssemblesFullCandidate() {
        LocalDateTime sourceTime = LocalDateTime.of(2026, 8, 1, 12, 0);

        EvidenceSubjectRow subject = new EvidenceSubjectRow();
        subject.setSubjectId(1L);
        subject.setName("Cowboy Bebop");
        subject.setNameCn("星际牛仔");
        subject.setType(2);
        subject.setNsfw(false);
        subject.setActive(true);
        subject.setSourceId(1_234);
        subject.setSourceUrl("https://bgm.tv/subject/1234");
        subject.setScore(new BigDecimal("8.9"));
        subject.setRank(10);
        subject.setRatingTotal(5000);
        subject.setCollectionTotal(20000);
        subject.setAirDate(LocalDate.of(1998, 4, 3));
        subject.setAirStatus("FINISHED");
        subject.setSummary("A group of bounty hunters...");
        subject.setSourceFetchedAt(sourceTime);

        EvidenceAliasRow alias = new EvidenceAliasRow();
        alias.setSubjectId(1L);
        alias.setName("カウボーイビバップ");

        EvidenceMetaTagRow metaTag = new EvidenceMetaTagRow();
        metaTag.setSubjectId(1L);
        metaTag.setName("SF");

        EvidenceCreditRow credit = new EvidenceCreditRow();
        credit.setSubjectId(1L);
        credit.setPersonName("Watanabe Shinichiro");
        credit.setRole("Director");
        credit.setRelation("MAIN");

        EvidenceCharacterRow character = new EvidenceCharacterRow();
        character.setSubjectId(1L);
        character.setCharacterName("Spike Spiegel");
        character.setRelation("MAIN");

        EvidenceRelationRow relation = new EvidenceRelationRow();
        relation.setSubjectId(1L);
        relation.setRelatedSubjectId(2L);
        relation.setRelatedSubjectName("Cowboy Bebop: Tengoku no Tobira");
        relation.setRelatedSubjectNameCn("天国之扉");
        relation.setRelation("side_story");

        when(evidenceMapper.selectSubjectBasics(List.of(1L))).thenReturn(List.of(subject));
        when(evidenceMapper.selectAliases(List.of(1L))).thenReturn(List.of(alias));
        when(evidenceMapper.selectMetaTags(List.of(1L))).thenReturn(List.of(metaTag));
        when(evidenceMapper.selectCredits(List.of(1L))).thenReturn(List.of(credit));
        when(evidenceMapper.selectCharacters(List.of(1L))).thenReturn(List.of(character));
        when(evidenceMapper.selectRelations(List.of(1L))).thenReturn(List.of(relation));

        List<EvidenceCandidateVO> result = evidenceService.batchEvidence(List.of(1L));

        assertThat(result).hasSize(1);
        EvidenceCandidateVO vo = result.get(0);
        assertThat(vo.getSubjectId()).isEqualTo(1L);
        assertThat(vo.getName()).isEqualTo("Cowboy Bebop");
        assertThat(vo.getNameCn()).isEqualTo("星际牛仔");
        assertThat(vo.getType()).isEqualTo(2);
        assertThat(vo.getNsfw()).isFalse();
        assertThat(vo.getActive()).isTrue();
        assertThat(vo.getSourceId()).isEqualTo(1_234);
        assertThat(vo.getSourceUrl()).isEqualTo("https://bgm.tv/subject/1234");
        assertThat(vo.getScore()).isEqualByComparingTo(new BigDecimal("8.9"));
        assertThat(vo.getRank()).isEqualTo(10);
        assertThat(vo.getRatingTotal()).isEqualTo(5000);
        assertThat(vo.getCollectionTotal()).isEqualTo(20000);
        assertThat(vo.getAirDate()).isEqualTo(LocalDate.of(1998, 4, 3));
        assertThat(vo.getAirStatus()).isEqualTo("FINISHED");
        assertThat(vo.getSummary()).isEqualTo("A group of bounty hunters...");
        assertThat(vo.getSourceTime()).isEqualTo(sourceTime);
        assertThat(vo.getSourceFetchedAt()).isEqualTo(sourceTime);

        assertThat(vo.getAliases()).containsExactly("カウボーイビバップ");
        assertThat(vo.getMetaTags()).containsExactly("SF");

        assertThat(vo.getCredits()).hasSize(1);
        assertThat(vo.getCredits().get(0).getPersonName()).isEqualTo("Watanabe Shinichiro");
        assertThat(vo.getCredits().get(0).getRole()).isEqualTo("Director");
        assertThat(vo.getCredits().get(0).getRelation()).isEqualTo("MAIN");

        assertThat(vo.getCharacters()).hasSize(1);
        assertThat(vo.getCharacters().get(0).getCharacterName()).isEqualTo("Spike Spiegel");
        assertThat(vo.getCharacters().get(0).getRelation()).isEqualTo("MAIN");

        assertThat(vo.getRelations()).hasSize(1);
        assertThat(vo.getRelations().get(0).getRelatedSubjectId()).isEqualTo(2L);
        assertThat(vo.getRelations().get(0).getRelatedSubjectName()).isEqualTo("Cowboy Bebop: Tengoku no Tobira");
        assertThat(vo.getRelations().get(0).getRelatedSubjectNameCn()).isEqualTo("天国之扉");
        assertThat(vo.getRelations().get(0).getRelation()).isEqualTo("side_story");
    }

/** 验证多条目证据聚合保持完整。 */
    @Test
    void batchEvidenceHandlesMultipleSubjects() {
        EvidenceSubjectRow s1 = new EvidenceSubjectRow();
        s1.setSubjectId(1L);
        s1.setName("Subject A");

        EvidenceSubjectRow s2 = new EvidenceSubjectRow();
        s2.setSubjectId(2L);
        s2.setName("Subject B");

        EvidenceAliasRow a1 = new EvidenceAliasRow();
        a1.setSubjectId(1L);
        a1.setName("Alias A");

        EvidenceAliasRow a2 = new EvidenceAliasRow();
        a2.setSubjectId(2L);
        a2.setName("Alias B");

        when(evidenceMapper.selectSubjectBasics(anyList())).thenReturn(List.of(s1, s2));
        when(evidenceMapper.selectAliases(anyList())).thenReturn(List.of(a1, a2));
        when(evidenceMapper.selectMetaTags(anyList())).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCredits(anyList())).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCharacters(anyList())).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectRelations(anyList())).thenReturn(Collections.emptyList());

        List<EvidenceCandidateVO> result = evidenceService.batchEvidence(List.of(1L, 2L));

        assertThat(result).hasSize(2);
        assertThat(result.get(0).getAliases()).containsExactly("Alias A");
        assertThat(result.get(1).getAliases()).containsExactly("Alias B");
        assertThat(result.get(0).getCredits()).isNull();
        assertThat(result.get(0).getCharacters()).isNull();
        assertThat(result.get(0).getRelations()).isNull();
    }

/** 验证重复条目标识只查询并返回一次。 */
    @Test
    void batchEvidenceDeduplicatesInputIds() {
        EvidenceSubjectRow s1 = new EvidenceSubjectRow();
        s1.setSubjectId(1L);
        s1.setName("Subject A");

        when(evidenceMapper.selectSubjectBasics(List.of(1L))).thenReturn(List.of(s1));
        when(evidenceMapper.selectAliases(List.of(1L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectMetaTags(List.of(1L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCredits(List.of(1L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCharacters(List.of(1L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectRelations(List.of(1L))).thenReturn(Collections.emptyList());

        evidenceService.batchEvidence(List.of(1L, 1L, 1L));

        verify(evidenceMapper).selectSubjectBasics(List.of(1L));
    }

/** 验证人物解析只展开有效且安全的条目。 */
    @Test
    void resolveEvidenceByPersonExpandsOnlyActiveSafeSubjects() {
        EvidenceSubjectRow subject = new EvidenceSubjectRow();
        subject.setSubjectId(11L);
        subject.setName("Person work");
        subject.setType(2);
        subject.setNsfw(false);
        subject.setActive(true);
        subject.setSourceId(101);

        when(evidenceMapper.selectSubjectIdsByPersonIds(List.of(7L))).thenReturn(List.of(11L, 11L));
        when(evidenceMapper.selectSubjectBasics(List.of(11L))).thenReturn(List.of(subject));
        when(evidenceMapper.selectAliases(List.of(11L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectMetaTags(List.of(11L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCredits(List.of(11L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCharacters(List.of(11L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectRelations(List.of(11L))).thenReturn(Collections.emptyList());

        List<EvidenceCandidateVO> result = evidenceService.resolveEvidence(
                new EvidenceEntityBatchRequestDTO(EvidenceEntityType.PERSON, List.of(7L)));

        assertThat(result).hasSize(1);
        assertThat(result.get(0).getSubjectId()).isEqualTo(11L);
        assertThat(result.get(0).getActive()).isTrue();
        assertThat(result.get(0).getSourceId()).isEqualTo(101);
        verify(evidenceMapper).selectSubjectIdsByPersonIds(List.of(7L));
        verify(evidenceMapper).selectSubjectBasics(List.of(11L));
    }

/** 验证角色与声优解析使用各自的查询路径。 */
    @Test
    void resolveEvidenceByCharacterAndActorUseDedicatedQueries() {
        when(evidenceMapper.selectSubjectIdsByCharacterIds(List.of(8L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectSubjectIdsByActorIds(List.of(9L))).thenReturn(List.of(12L));

        EvidenceSubjectRow subject = new EvidenceSubjectRow();
        subject.setSubjectId(12L);
        subject.setName("Actor work");
        subject.setType(2);
        subject.setNsfw(false);
        when(evidenceMapper.selectSubjectBasics(List.of(12L))).thenReturn(List.of(subject));
        when(evidenceMapper.selectAliases(List.of(12L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectMetaTags(List.of(12L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCredits(List.of(12L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCharacters(List.of(12L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectRelations(List.of(12L))).thenReturn(Collections.emptyList());

        assertThat(evidenceService.resolveEvidence(
                new EvidenceEntityBatchRequestDTO(EvidenceEntityType.CHARACTER, List.of(8L)))).isEmpty();
        assertThat(evidenceService.resolveEvidence(
                new EvidenceEntityBatchRequestDTO(EvidenceEntityType.ACTOR, List.of(9L))))
                .extracting(EvidenceCandidateVO::getSubjectId)
                .containsExactly(12L);
        verify(evidenceMapper).selectSubjectIdsByCharacterIds(List.of(8L));
        verify(evidenceMapper).selectSubjectIdsByActorIds(List.of(9L));
    }

/** 验证关联条目解析使用双向关系查询。 */
    @Test
    void resolveEvidenceByRelatedSubjectsUsesBidirectionalRelationQuery() {
        EvidenceSubjectRow subject = new EvidenceSubjectRow();
        subject.setSubjectId(20L);
        subject.setName("Related work");
        subject.setType(2);
        subject.setNsfw(false);
        subject.setActive(true);

        when(evidenceMapper.selectRelatedSubjectIds(List.of(10L))).thenReturn(List.of(20L));
        when(evidenceMapper.selectSubjectBasics(List.of(20L))).thenReturn(List.of(subject));
        when(evidenceMapper.selectAliases(List.of(20L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectMetaTags(List.of(20L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCredits(List.of(20L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectCharacters(List.of(20L))).thenReturn(Collections.emptyList());
        when(evidenceMapper.selectRelations(List.of(20L))).thenReturn(Collections.emptyList());

        List<EvidenceCandidateVO> result = evidenceService.resolveEvidence(
                new EvidenceEntityBatchRequestDTO(EvidenceEntityType.RELATION_SUBJECT, List.of(10L)));

        assertThat(result).extracting(EvidenceCandidateVO::getSubjectId).containsExactly(20L);
        verify(evidenceMapper).selectRelatedSubjectIds(List.of(10L));
    }

/** 验证空请求返回空结果且超量请求被拒绝。 */
    @Test
    void resolveEvidenceReturnsEmptyForNullRequestAndRejectsTooManyIds() {
        assertThat(evidenceService.resolveEvidence(null)).isEmpty();

        EvidenceEntityBatchRequestDTO request = new EvidenceEntityBatchRequestDTO(
                EvidenceEntityType.SUBJECT, java.util.stream.LongStream.rangeClosed(1, 51).boxed().toList());
        org.assertj.core.api.Assertions.assertThatThrownBy(() -> evidenceService.resolveEvidence(request))
                .isInstanceOf(top.zhaizz.common.exception.BizException.class)
                .hasMessageContaining("最多 50");
    }
}
