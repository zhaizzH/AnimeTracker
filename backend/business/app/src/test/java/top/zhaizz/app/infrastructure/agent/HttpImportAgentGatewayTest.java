package top.zhaizz.app.infrastructure.agent;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class HttpImportAgentGatewayTest {
    private MockRestServiceServer server;
    private HttpImportAgentGateway gateway;

    @BeforeEach
    void setUp() {
        RestTemplate restTemplate = new RestTemplate();
        server = MockRestServiceServer.bindTo(restTemplate).build();
        AgentProperties properties = new AgentProperties();
        properties.setBaseUrl("http://agent");
        gateway = new HttpImportAgentGateway(restTemplate, properties);
    }

    @Test
    void forwardsAuthorizationAndEncodedQueryParameters() {
        server.expect(requestTo("http://agent/api/admin/agent/import/run"
                        + "?mode=season&key=2026-summer&workers=4"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header("Authorization", "Bearer token"))
                .andRespond(withSuccess());
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("season");
        request.setKey("2026-summer");
        request.setWorkers(4);

        gateway.runImport("Bearer token", request);

        server.verify();
    }

    @Test
    void mapsUpstreamConflictToExistingBusinessError() {
        server.expect(requestTo("http://agent/api/admin/agent/import/run?mode=full"))
                .andRespond(withStatus(HttpStatus.CONFLICT));
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("full");

        BizException error = assertThrows(BizException.class,
                () -> gateway.runImport(null, request));

        assertThat(error.getCode()).isEqualTo(ErrorType.CONFLICT.getCode());
        assertThat(error.getMessage()).isEqualTo("已有导入任务运行中");
        server.verify();
    }
}
