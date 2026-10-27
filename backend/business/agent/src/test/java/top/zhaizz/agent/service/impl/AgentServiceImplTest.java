package top.zhaizz.agent.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.catchThrowable;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;

/** Agent 代理的 GET SSE 转发与上游 409 结构化透传回归 */
class AgentServiceImplTest {

    /** 记录上游实际收到的请求方法 */
    private final AtomicReference<String> seenMethod = new AtomicReference<>();
    /** 记录上游实际收到的查询串 */
    private final AtomicReference<String> seenQuery = new AtomicReference<>();
    /** 记录上游实际收到的请求体 */
    private final AtomicReference<String> seenBody = new AtomicReference<>();
    /** 记录上游实际收到的 Content-Type */
    private final AtomicReference<String> seenContentType = new AtomicReference<>();
    /** 本用例启动的本地 HTTP 服务，用例结束必须关闭 */
    private HttpServer server;

    /** 每个用例结束后释放本地端口 */
    @AfterEach
    void stopServer() {
        if (server != null) {
            server.stop(0);
        }
    }

    /**
     * 启动一个记录请求细节的本地端点
     *
     * @param path 监听路径
     * @param status 返回的 HTTP 状态
     * @param contentType 响应 Content-Type
     * @param payload 响应正文
     * @return 已启动的服务
     * @throws IOException 端口绑定失败时抛出
     */
    private HttpServer startServer(String path, int status, String contentType, String payload) throws IOException {
        server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext(path, exchange -> {
            seenMethod.set(exchange.getRequestMethod());
            seenQuery.set(exchange.getRequestURI().getRawQuery());
            seenBody.set(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
            seenContentType.set(exchange.getRequestHeaders().getFirst("Content-Type"));
            byte[] bytes = payload.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", contentType);
            exchange.sendResponseHeaders(status, bytes.length == 0 ? -1 : bytes.length);
            try (OutputStream output = exchange.getResponseBody()) {
                output.write(bytes);
            }
        });
        server.start();
        return server;
    }

    /**
     * 创建指向本地端点的被测服务
     *
     * @param restTemplate 普通请求客户端
     * @return 以本地服务为上游的代理实现
     */
    private AgentServiceImpl service(RestTemplate restTemplate) {
        return new AgentServiceImpl(restTemplate, new ObjectMapper(),
                "http://localhost:" + server.getAddress().getPort(), 1000);
    }

    /**
     * 从异常附加数据里读出 active_run_id
     *
     * @param error 上游 409 转换出的业务异常
     * @return detail.active_run_id；结构不符时断言失败
     */
    private Object activeRunId(BizException error) {
        assertThat(error.getData()).isInstanceOf(Map.class);
        @SuppressWarnings("unchecked")
        Map<String, Object> detail = (Map<String, Object>) error.getData();
        return detail.get("active_run_id");
    }

    /** GET 重连必须带 after 查询、无请求体且不声明 JSON Content-Type，SSE 行原样交给消费器 */
    @Test
    void streamGetSendsQueryWithoutBody() throws Exception {
        startServer("/api/client/agent/runs/r1/stream", 200,
                MediaType.TEXT_EVENT_STREAM_VALUE, "data: {\"type\":\"answer\"}\n\n");
        AgentServiceImpl service = service(new RestTemplate());
        List<String> lines = new ArrayList<>();

        service.streamGet("/api/client/agent/runs/r1/stream", "after=3", "Bearer token", lines::add);

        assertThat(seenMethod.get()).isEqualTo("GET");
        assertThat(seenQuery.get()).isEqualTo("after=3");
        assertThat(seenBody.get()).isEmpty();
        assertThat(seenContentType.get()).isNull();
        assertThat(lines).contains("data: {\"type\":\"answer\"}");
    }

    /** 上游 409 的 detail 必须进入异常 data，前端才能拿到 active_run_id 做打断并插入 */
    @Test
    void streamGetConflictExposesActiveRunId() throws Exception {
        startServer("/api/client/agent/runs/r1/stream", 409, MediaType.APPLICATION_JSON_VALUE,
                "{\"detail\":{\"active_run_id\":\"abc\",\"status\":\"running\",\"capabilities\":[\"interrupt\"]}}");
        AgentServiceImpl service = service(new RestTemplate());

        Throwable thrown = catchThrowable(
                () -> service.streamGet("/api/client/agent/runs/r1/stream", "after=0", "Bearer token", line -> { }));

        assertThat(thrown).isInstanceOf(BizException.class);
        BizException error = (BizException) thrown;
        assertThat(error.getCode()).isEqualTo(409);
        assertThat(activeRunId(error)).isEqualTo("abc");
    }

    /** 普通 POST /stream 的 409 同样保留结构化 detail，且 message 不拼接上游原文 */
    @Test
    void exchangeConflictExposesDetailWithoutLeakingRawBody() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer mock = MockRestServiceServer.bindTo(restTemplate).build();
        mock.expect(requestTo("http://agent/api/client/agent/stream"))
                .andRespond(withStatus(HttpStatus.CONFLICT).contentType(MediaType.APPLICATION_JSON)
                        .body("{\"detail\":{\"active_run_id\":\"abc\",\"status\":\"running\"}}"));
        AgentServiceImpl service = new AgentServiceImpl(restTemplate, new ObjectMapper(), "http://agent", 1000);

        Throwable thrown = catchThrowable(
                () -> service.exchange("/api/client/agent/stream", HttpMethod.POST, "Bearer token", Map.of()));

        assertThat(thrown).isInstanceOf(BizException.class);
        BizException error = (BizException) thrown;
        assertThat(error.getCode()).isEqualTo(ErrorType.CONFLICT.getCode());
        assertThat(activeRunId(error)).isEqualTo("abc");
        assertThat(error.getMessage()).doesNotContain("abc").doesNotContain("detail");
    }

    /** 上游 409 但 body 不是可解析的 detail 对象时降级为无 data，不得因此抛解析异常 */
    @Test
    void exchangeConflictWithoutDetailHasNoData() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer mock = MockRestServiceServer.bindTo(restTemplate).build();
        mock.expect(requestTo("http://agent/api/client/agent/stream"))
                .andRespond(withStatus(HttpStatus.CONFLICT).contentType(MediaType.TEXT_PLAIN).body("conflict"));
        AgentServiceImpl service = new AgentServiceImpl(restTemplate, new ObjectMapper(), "http://agent", 1000);

        Throwable thrown = catchThrowable(
                () -> service.exchange("/api/client/agent/stream", HttpMethod.POST, "Bearer token", Map.of()));

        assertThat(thrown).isInstanceOf(BizException.class);
        BizException error = (BizException) thrown;
        assertThat(error.getCode()).isEqualTo(409);
        assertThat(error.getData()).isNull();
    }

    /** 上游 409 body 为 JSON null 时同样降级为无 data，不产生二次解析异常 */
    @Test
    void exchangeConflictWithNullPayloadHasNoData() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer mock = MockRestServiceServer.bindTo(restTemplate).build();
        mock.expect(requestTo("http://agent/api/client/agent/stream"))
                .andRespond(withStatus(HttpStatus.CONFLICT).contentType(MediaType.APPLICATION_JSON).body("null"));
        AgentServiceImpl service = new AgentServiceImpl(restTemplate, new ObjectMapper(), "http://agent", 1000);

        Throwable thrown = catchThrowable(
                () -> service.exchange("/api/client/agent/stream", HttpMethod.POST, "Bearer token", Map.of()));

        assertThat(thrown).isInstanceOf(BizException.class);
        BizException error = (BizException) thrown;
        assertThat(error.getCode()).isEqualTo(409);
        assertThat(error.getData()).isNull();
    }

    /** 其他 4xx 映射不回归：404 仍是 NOT_FOUND 且不携带上游 body */
    @Test
    void exchangeNotFoundMappingIsUnchanged() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer mock = MockRestServiceServer.bindTo(restTemplate).build();
        mock.expect(requestTo("http://agent/api/client/agent/sessions/s1/run"))
                .andRespond(withStatus(HttpStatus.NOT_FOUND).contentType(MediaType.APPLICATION_JSON)
                        .body("{\"detail\":\"run 不存在或无权限\"}"));
        AgentServiceImpl service = new AgentServiceImpl(restTemplate, new ObjectMapper(), "http://agent", 1000);

        Throwable thrown = catchThrowable(
                () -> service.exchange("/api/client/agent/sessions/s1/run", HttpMethod.GET, "Bearer token", null));

        assertThat(thrown).isInstanceOf(BizException.class);
        BizException error = (BizException) thrown;
        assertThat(error.getCode()).isEqualTo(404);
        assertThat(error.getData()).isNull();
    }
}
