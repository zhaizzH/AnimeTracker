package top.zhaizz.app.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import top.zhaizz.agent.constant.TraceConstants;

import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * 请求级 traceId：接受合法 X-Request-ID 或生成 UUID，写入 MDC 与响应头；请求结束清理 MDC
 * 限制字符集防止日志注入；不合法或缺失时生成新 UUID
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdFilter extends OncePerRequestFilter {

    /** 请求 ID 的格式校验模式 */
    private static final Pattern VALID_ID = Pattern.compile("^[A-Za-z0-9._-]{1,128}$");

    /**
     * 校验并透传请求 ID，同时维护请求追踪上下文的生命周期
     *
     * @param request 包含可选追踪请求头的当前 HTTP 请求
     * @param response 待写入内容的 HTTP 响应
     * @param chain 后续 Servlet 过滤链
     * @throws jakarta.servlet.ServletException 后续过滤链处理失败时抛出
     * @throws IOException 后续请求或响应读写失败时抛出
     */
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String traceId = sanitize(request.getHeader(TraceConstants.HEADER_X_REQUEST_ID));
        MDC.put(TraceConstants.MDC_TRACE_ID, traceId);
        response.setHeader(TraceConstants.HEADER_X_REQUEST_ID, traceId);
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove(TraceConstants.MDC_TRACE_ID);
        }
    }

    /**
     * 清理请求头中的追踪 ID，仅保留可安全写入 MDC 和响应头的内容
     *
     * @param value 原始追踪 ID
     * @return 清理后的追踪 ID；无效或空值生成新的 UUID
     */
    private String sanitize(String value) {
        if (value != null && VALID_ID.matcher(value.trim()).matches()) {
            return value.trim();
        }
        return UUID.randomUUID().toString();
    }
}
