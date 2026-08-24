package top.zhaizz.agent.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.config.AgentProperties;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.constant.TraceConstants;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.Result;

import java.net.SocketTimeoutException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.springframework.test.web.client.ExpectedCount.once;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class HttpAgentGatewayTest {

    private RestTemplate restTemplate;
    private MockRestServiceServer server;
    private HttpAgentGateway gateway;

    @BeforeEach
    void setUp() {
        restTemplate = new RestTemplate();
        server = MockRestServiceServer.bindTo(restTemplate).build();

        AgentProperties props = new AgentProperties();
        props.setBaseUrl("http://agent");
        gateway = new HttpAgentGateway(restTemplate, props, new ObjectMapper());
    }

    @AfterEach
    void tearDown() {
        MDC.clear();
    }

    @Test
    void exchangeWrapsAgentJsonObjectWithoutExposingRestResponse() {
        server.expect(once(), requestTo("http://agent/api/client/agent/health"))
                .andExpect(method(HttpMethod.GET))
                .andExpect(header("Authorization", "Bearer token"))
                .andRespond(withSuccess("{\"ok\":true}", MediaType.APPLICATION_JSON));

        Result<?> result = gateway.exchange("/api/client/agent/health", HttpMethod.GET, "Bearer token", null);

        assertThat(result.getCode()).isEqualTo(200);
        assertThat(result.getData()).isEqualTo(Map.of("ok", true));
        server.verify();
    }

    @Test
    void exchangeSerializesBodyAndWrapsJsonArray() {
        server.expect(once(), requestTo("http://agent/api/client/agent/sessions"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().json("{\"name\":\"s1\"}"))
                .andRespond(withSuccess("[{\"id\":\"s1\"}]", MediaType.APPLICATION_JSON));

        Result<?> result = gateway.exchange(
                "/api/client/agent/sessions", HttpMethod.POST, "Bearer token", Map.of("name", "s1"));

        assertThat(result.getData()).isEqualTo(List.of(Map.of("id", "s1")));
        server.verify();
    }

    @Test
    void exchangeMapsUpstreamNotFoundWithoutExposingBody() {
        server.expect(once(), requestTo("http://agent/api/client/agent/sessions/missing"))
                .andRespond(withStatus(HttpStatus.NOT_FOUND).body("private upstream body"));

        BizException error = assertThrows(BizException.class, () ->
                gateway.exchange("/api/client/agent/sessions/missing", HttpMethod.GET, "Bearer token", null));

        assertThat(error.getCode()).isEqualTo(ErrorType.NOT_FOUND.getCode());
        assertThat(error.getMessage()).doesNotContain("private upstream body");
        server.verify();
    }

    @Test
    void exchangeMapsConnectionFailureToServiceUnavailable() {
        server.expect(once(), requestTo("http://agent/api/client/agent/health"))
                .andRespond(request -> {
                    throw new ResourceAccessException("connect timeout", new SocketTimeoutException("timeout"));
                });

        BizException error = assertThrows(BizException.class, () ->
                gateway.exchange("/api/client/agent/health", HttpMethod.GET, null, null));

        assertThat(error.getCode()).isEqualTo(ErrorType.SERVICE_UNAVAILABLE.getCode());
    }

    @Test
    void exchangeMaps5xxToServiceUnavailableAnd401ToUnauthorized() {
        assertThat(mapExchangeError(new HttpServerErrorException(HttpStatus.INTERNAL_SERVER_ERROR)))
                .isEqualTo(ErrorType.SERVICE_UNAVAILABLE.getCode());
        assertThat(mapExchangeError(new HttpClientErrorException(HttpStatus.UNAUTHORIZED)))
                .isEqualTo(ErrorType.UNAUTHORIZED.getCode());
    }

    @Test
    void streamForwardsTraceIdAndEachSseLine() {
        RestTemplate streamTemplate = new RestTemplate();
        MockRestServiceServer streamServer = MockRestServiceServer.bindTo(streamTemplate).build();
        ReflectionTestUtils.setField(gateway, "streamRestTemplate", streamTemplate);

        MDC.put(TraceConstants.MDC_TRACE_ID, "trace-7");
        streamServer.expect(once(), requestTo("http://agent/api/client/agent/stream"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header("Authorization", "Bearer token"))
                .andExpect(header(TraceConstants.HEADER_X_REQUEST_ID, "trace-7"))
                .andExpect(content().json("{\"sessionId\":\"s1\",\"content\":\"hi\"}"))
                .andRespond(withSuccess("data: {\"type\":\"answer\"}\n\n", MediaType.TEXT_EVENT_STREAM));

        List<String> lines = new ArrayList<>();
        gateway.stream("/api/client/agent/stream", HttpMethod.POST,
                "Bearer token", Map.of("sessionId", "s1", "content", "hi"), lines::add);

        assertThat(lines).containsExactly("data: {\"type\":\"answer\"}", "");
        streamServer.verify();
    }

    private int mapExchangeError(RuntimeException exception) {
        RestTemplate failingRestTemplate = new RestTemplate();
        MockRestServiceServer failingServer = MockRestServiceServer.bindTo(failingRestTemplate).build();
        AgentProperties props = new AgentProperties();
        props.setBaseUrl("http://agent");
        HttpAgentGateway failingGateway = new HttpAgentGateway(failingRestTemplate, props, new ObjectMapper());
        failingServer.expect(once(), requestTo("http://agent/api/x"))
                .andRespond(request -> {
                    throw exception;
                });

        BizException error = assertThrows(BizException.class,
                () -> failingGateway.exchange("/api/x", HttpMethod.GET, null, null));
        return error.getCode();
    }
}
