package top.zhaizz.client.service.impl;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.jdbc.BadSqlGrammarException;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.mapper.SubjectRelationMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.model.LexicalSearchRow;
import top.zhaizz.client.model.SearchIndexReleaseRow;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.subject.LexicalSearchRequestDTO;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.vo.subject.LexicalSearchResultVO;
import top.zhaizz.pojo.vo.subject.SubjectBatchResultVO;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

/** 用户端词法检索版本和安全边界测试 */
@ExtendWith(MockitoExtension.class)
class ClientSubjectServiceLexicalTest {

    /** 模拟条目及发布版本查询 */
    @Mock
    private SubjectMapper subjectMapper;
    /** 模拟条目标签查询 */
    @Mock
    private SubjectTagMapper subjectTagMapper;
    /** 模拟关联条目查询 */
    @Mock
    private SubjectRelationMapper subjectRelationMapper;
    /** 模拟用户收藏查询 */
    @Mock
    private CollectionMapper collectionMapper;

    /** 被测条目检索服务 */
    @InjectMocks
    private ClientSubjectServiceImpl subjectService;

/** 验证词法检索返回发布版本并保持确定性排序 */
    @Test
    void lexicalSearchReturnsReleaseVersionAndDeterministicRank() {
        SearchIndexReleaseRow release = new SearchIndexReleaseRow();
        release.setIndexVersion("v2026-09");
        release.setProfileVersion("subject-v2");
        LexicalSearchRow row = new LexicalSearchRow();
        row.setSubjectId(42L);
        row.setName("Cowboy Bebop");
        row.setNameCn("星际牛仔");
        row.setLexicalScore(new BigDecimal("3.25"));
        when(subjectMapper.selectActiveSearchIndexRelease()).thenReturn(release);
        when(subjectMapper.lexicalSearch("牛仔", List.of("科幻"), null, null, null, null,
                List.of(42L), "v2026-09", 10)).thenReturn(List.of(row));

        LexicalSearchRequestDTO request = new LexicalSearchRequestDTO();
        request.setQ(" 牛仔 ");
        request.setTags(List.of("科幻"));
        request.setSubjectIds(List.of(42L));
        request.setLimit(10);

        LexicalSearchResultVO result = subjectService.lexicalSearch(request);

        assertThat(result.getIndexVersion()).isEqualTo("v2026-09");
        assertThat(result.getProfileVersion()).isEqualTo("subject-v2");
        assertThat(result.getCandidates()).hasSize(1);
        assertThat(result.getCandidates().get(0).getRank()).isEqualTo(1);
        assertThat(result.getCandidates().get(0).getLexicalScore()).isEqualByComparingTo("3.25");
    }

/** 验证词法投影不完整或无发布版本时安全降级 */
    @Test
    void lexicalSearchFailsClosedWhenNoReleaseIsActive() {
        when(subjectMapper.selectActiveSearchIndexRelease()).thenReturn(null);

        LexicalSearchRequestDTO request = new LexicalSearchRequestDTO();
        request.setQ("测试");

        assertThatThrownBy(() -> subjectService.lexicalSearch(request))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("词法索引尚未发布");
    }

/** 验证词法投影不完整或无发布版本时安全降级 */
    @Test
    void lexicalSearchFailsClosedWhenProjectionMigrationIsMissing() {
        when(subjectMapper.selectActiveSearchIndexRelease())
                .thenThrow(new BadSqlGrammarException("select release", "missing table", null));

        LexicalSearchRequestDTO request = new LexicalSearchRequestDTO();
        request.setQ("测试");

        assertThatThrownBy(() -> subjectService.lexicalSearch(request))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("尚未迁移");
    }

/** 验证批量条目结果暴露 Agent 权威检查所需的有效标记 */
    @Test
    void batchSubjectsExposesActiveFlagForAgentAuthorityChecks() {
        Subject subject = new Subject();
        subject.setId(42L);
        subject.setType(2);
        subject.setNsfw(false);
        subject.setImportStatus(1);
        when(subjectMapper.selectBatchIds(List.of(42L))).thenReturn(List.of(subject));

        SubjectBatchResultVO result = subjectService.batch(List.of(42L), false, null);

        assertThat(result.getItems()).hasSize(1);
        assertThat(result.getItems().get(0).getActive()).isTrue();
    }
}
