package top.zhaizz.client.mapper;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;

/** 证据 Mapper SQL 兼容性测试 */
class EvidenceMapperSqlCompatibilityTest {

/** 验证实体展开 SQL 在 MySQL 8.4 上可按评分排序 */
    @Test
    void entityExpansionQueriesCanOrderByScoreOnMysql84() throws IOException {
        String xml;
        try (InputStream stream = getClass().getClassLoader().getResourceAsStream(
                "mapper/EvidenceMapper.xml")) {
            assertThat(stream).as("EvidenceMapper.xml must be on the test classpath").isNotNull();
            xml = new String(stream.readAllBytes(), StandardCharsets.UTF_8)
                    .replace("\r\n", "\n");
        }

        assertThat(xml)
                .contains("<select id=\"selectSubjectIdsByPersonIds\" resultType=\"java.lang.Long\">")
                .contains("<select id=\"selectSubjectIdsByCharacterIds\" resultType=\"java.lang.Long\">")
                .contains("<select id=\"selectSubjectIdsByActorIds\" resultType=\"java.lang.Long\">")
                .doesNotContain("SELECT DISTINCT s.id");

        assertThat(countOccurrences(xml, "GROUP BY s.id, s.score\n        ORDER BY s.score DESC, s.id ASC"))
                .as("PERSON, CHARACTER and ACTOR queries must group the sort column")
                .isEqualTo(3);
    }

    /**
     * 统计 SQL 片段非重叠出现次数
     * @param text 待检查的 Mapper XML
     * @param needle 非空 SQL 片段
     * @return 片段匹配次数
     */
    private static int countOccurrences(String text, String needle) {
        int count = 0;
        int offset = 0;
        while ((offset = text.indexOf(needle, offset)) >= 0) {
            count++;
            offset += needle.length();
        }
        return count;
    }
}
