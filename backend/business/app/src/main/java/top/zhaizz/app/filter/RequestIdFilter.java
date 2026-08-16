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
import top.zhaizz.common.constant.TraceConstants;

import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * 请求级 traceId：接受合法 X-Request-ID 或生成 UUID，写入 MDC 与响应头；请求结束清理 MDC。
 * 限制字符集防止日志注入；不合法或缺失时生成新 UUID。
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdFilter extends OncePerRequestFilter {

    private static final Pattern VALID_ID = Pattern.compile("^[A-Za-z0-9._-]{1,128}$");

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

    private String sanitize(String value) {
        if (value != null && VALID_ID.matcher(value.trim()).matches()) {
            return value.trim();
        }
        return UUID.randomUUID().toString();
    }
}
