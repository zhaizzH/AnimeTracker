package top.zhaizz.agent.gateway;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.http.*;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;
import java.io.IOException;
import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

/** 导入 HTTP 网关的请求协议、错误分类和上游隐私回归。 */
class HttpImportAgentGatewayTest {
    /** 每个用例独立的 HTTP 客户端。 */
    private final RestTemplate rest = new RestTemplate();
    /** 拦截 HTTP 请求，无需连接真实 Agent。 */
    private final MockRestServiceServer server = MockRestServiceServer.bindTo(rest).build();
    /** 被测导入适配器。 */
    private final HttpImportAgentGateway gateway = new HttpImportAgentGateway(rest, "http://agent");

    /** 完整参数以查询字符串传递，鉴权头原样转发且不发送请求体。 */
    @Test
    void forwardsImportRequest() {
        ImportRunDTO request = request();
        request.setKey("2026-summer");
        request.setSince("2026-01-01");
        request.setWorkers(4);
        server.expect(requestTo("http://agent/api/admin/agent/import/run?mode=recent&key=2026-summer&since=2026-01-01&workers=4"))
                .andExpect(method(HttpMethod.POST)).andExpect(header("Authorization", "Bearer test"))
                .andExpect(content().string(""))
                .andRespond(withSuccess("{}", MediaType.APPLICATION_JSON));
        gateway.runImport("Bearer test", request);
        server.verify();
    }

    /** 可选参数和凭据缺失时不发送空查询值或鉴权头。 */
    @Test
    void omitsAbsentOptions() {
        server.expect(requestTo("http://agent/api/admin/agent/import/run?mode=recent"))
                .andExpect(headerDoesNotExist("Authorization"))
                .andRespond(withSuccess());
        gateway.runImport(null, request());
        server.verify();
    }

    /**
     * 上游状态码归并为业务错误，私有响应体不会进入返回异常。
     * @param status 上游 HTTP 状态码
     * @param code 预期业务错误码
     * @param message 面向用户的固定错误说明
     */
    @ParameterizedTest
    @CsvSource({"409,409,已有导入任务运行中", "400,400,导入任务启动失败", "403,400,导入任务启动失败", "500,500,导入任务启动失败", "503,500,导入任务启动失败"})
    void classifiesErrorsWithoutLeakingBody(int status, int code, String message) {
        server.expect(anything()).andRespond(withStatus(HttpStatus.valueOf(status))
                .body("private-token-and-upstream-stack"));
        BizException error = catchThrowableOfType(() -> gateway.runImport(null, request()), BizException.class);
        assertThat(error.getCode()).isEqualTo(code);
        assertThat(error).hasMessage(message).hasNoCause();
        assertThat(error.getData()).isNull();
        server.verify();
    }

    /** 连接失败转换为统一内部错误，底层网络细节不返回调用方。 */
    @Test
    void classifiesConnectionFailure() {
        server.expect(anything()).andRespond(withException(new IOException("private-network-detail")));
        BizException error = catchThrowableOfType(() -> gateway.runImport(null, request()), BizException.class);
        assertThat(error.getCode()).isEqualTo(500);
        assertThat(error).hasMessage("Agent 导入服务连接失败").hasNoCause();
        server.verify();
    }

    /**
     * 创建只含必填模式的导入请求。
     * @return 最近更新导入参数
     */
    private static ImportRunDTO request() {
        ImportRunDTO request = new ImportRunDTO();
        request.setMode("recent");
        return request;
    }
}
