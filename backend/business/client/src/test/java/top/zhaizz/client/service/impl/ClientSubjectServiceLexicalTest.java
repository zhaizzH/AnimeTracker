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
import top.zhaizz.pojo.vo.subject.LexicalSearchResultVO;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ClientSubjectServiceLexicalTest {

    @Mock
    private SubjectMapper subjectMapper;
    @Mock
    private SubjectTagMapper subjectTagMapper;
    @Mock
    private SubjectRelationMapper subjectRelationMapper;
    @Mock
    private CollectionMapper collectionMapper;

    @InjectMocks
    private ClientSubjectServiceImpl subjectService;

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

    @Test
    void lexicalSearchFailsClosedWhenNoReleaseIsActive() {
        when(subjectMapper.selectActiveSearchIndexRelease()).thenReturn(null);

        LexicalSearchRequestDTO request = new LexicalSearchRequestDTO();
        request.setQ("测试");

        assertThatThrownBy(() -> subjectService.lexicalSearch(request))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("词法索引尚未发布");
    }

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
}
