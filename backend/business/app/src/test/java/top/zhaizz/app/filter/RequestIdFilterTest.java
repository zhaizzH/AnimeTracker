package top.zhaizz.app.filter;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import top.zhaizz.common.constant.TraceConstants;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * RequestIdFilter 测试：合法 ID 回显并写入 MDC，缺失/非法时生成 UUID，请求结束清理 MDC。
 */
class RequestIdFilterTest {

    private final RequestIdFilter filter = new RequestIdFilter();

    private String runFilter(String headerValue) throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest();
        if (headerValue != null) {
            request.addHeader(TraceConstants.HEADER_X_REQUEST_ID, headerValue);
        }
        MockHttpServletResponse response = new MockHttpServletResponse();
        String[] capturedMdc = new String[1];
        FilterChain chain = (req, res) -> capturedMdc[0] = MDC.get(TraceConstants.MDC_TRACE_ID);

        filter.doFilter(request, response, chain);

        assertThat(capturedMdc[0]).isEqualTo(response.getHeader(TraceConstants.HEADER_X_REQUEST_ID));
        // 请求结束必须清理 MDC，避免线程复用污染
        assertThat(MDC.get(TraceConstants.MDC_TRACE_ID)).isNull();
        return response.getHeader(TraceConstants.HEADER_X_REQUEST_ID);
    }

    @Test
    void validIncomingIdIsEchoedAndPlacedInMdc() throws Exception {
        assertThat(runFilter("req-123")).isEqualTo("req-123");
    }

    @Test
    void missingHeaderGeneratesUuid() throws Exception {
        String traceId = runFilter(null);
        assertThat(UUID.fromString(traceId)).isNotNull();
    }

    @Test
    void invalidHeaderGeneratesUuid() throws Exception {
        // 含空格/控制字符的非法 ID 拒绝透传，防止日志注入
        String traceId = runFilter("bad id!\n<script>");
        assertThat(UUID.fromString(traceId)).isNotNull();
    }
}
