package top.zhaizz.client.mapper;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;

class SubjectMapperLexicalSqlCompatibilityTest {

    @Test
    void lexicalQueryUsesBoundParametersAndActiveRelease() throws IOException {
        String xml;
        try (InputStream stream = getClass().getClassLoader().getResourceAsStream("mapper/SubjectMapper.xml")) {
            assertThat(stream).as("SubjectMapper.xml must be on the test classpath").isNotNull();
            xml = new String(stream.readAllBytes(), StandardCharsets.UTF_8).replace("\r\n", "\n");
        }

        assertThat(xml)
                .contains("<select id=\"selectActiveSearchIndexRelease\"")
                .contains("<select id=\"lexicalSearch\"")
                .contains("MATCH(d.title, d.aliases, d.lexical_text)")
                .contains("r.profile_version = d.profile_version")
                .contains("r.status = 'ACTIVE'")
                .contains("r.active_slot = 1")
                .contains("LIMIT #{limit}")
                .doesNotContain("${query}")
                .doesNotContain("${indexVersion}")
                .doesNotContain("${limit}");
    }
}
