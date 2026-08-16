package top.zhaizz.common.constant;

/**
 * 请求级 trace 相关常量（Business 与 Agent 共享同一 X-Request-ID 语义）
 */
public final class TraceConstants {

    /** MDC 中的 traceId 键 */
    public static final String MDC_TRACE_ID = "traceId";
    /** HTTP 请求头名称 */
    public static final String HEADER_X_REQUEST_ID = "X-Request-ID";

    private TraceConstants() {
    }
}
