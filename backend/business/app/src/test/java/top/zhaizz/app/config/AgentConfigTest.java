package top.zhaizz.app.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.agent.service.impl.AgentServiceImpl;
import top.zhaizz.common.constant.TraceConstants;

import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class AgentConfigTest {

    @AfterEach
    void clearMdc() {
        MDC.clear();
    }

    @Test
    void configuresTimeoutsAndForwardsTraceHeader() {
        AgentProperties properties = new AgentProperties();
        properties.setConnectTimeout(1200);
        properties.setReadTimeout(3400);
        RestTemplate restTemplate = new AgentConfig().restTemplate(new RestTemplateBuilder(), properties);
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();
        MDC.put(TraceConstants.MDC_TRACE_ID, "trace-test");
        server.expect(requestTo("http://agent.test/health"))
                .andExpect(header(TraceConstants.HEADER_X_REQUEST_ID, "trace-test"))
                .andRespond(withSuccess("{}", MediaType.APPLICATION_JSON));

        restTemplate.getForEntity("http://agent.test/health", String.class);

        server.verify();
    }

    @Test
    void streamsAfterNormalReadTimeoutWithoutTimingOut() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/stream", exchange -> {
            exchange.getResponseHeaders().set("Content-Type", MediaType.TEXT_EVENT_STREAM_VALUE);
            exchange.sendResponseHeaders(200, 0);
            try (OutputStream output = exchange.getResponseBody()) {
                try {
                    Thread.sleep(300);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    return;
                }
                output.write("data: ready\n".getBytes(StandardCharsets.UTF_8));
                output.flush();
            }
        });
        server.start();

        try {
            AgentProperties properties = new AgentProperties();
            properties.setBaseUrl("http://localhost:" + server.getAddress().getPort());
            properties.setConnectTimeout(1000);
            properties.setReadTimeout(100);
            AgentServiceImpl service = new AgentServiceImpl(
                    new RestTemplate(), new ObjectMapper(), properties.getBaseUrl(), properties.getConnectTimeout());
            List<String> lines = new ArrayList<>();

            service.stream("/stream", HttpMethod.GET, null, null, lines::add);

            assertThat(lines).containsExactly("data: ready");
        } finally {
            server.stop(0);
        }
    }
}
