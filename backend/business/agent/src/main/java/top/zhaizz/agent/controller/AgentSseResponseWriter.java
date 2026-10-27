package top.zhaizz.agent.controller;

import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.io.PrintWriter;
import java.io.UncheckedIOException;
import java.util.function.Consumer;

/** 为 Agent SSE 代理提供延迟提交响应和逐行写出的共同实现 */
final class AgentSseResponseWriter {

    /** 禁止实例化仅包含 SSE 写出逻辑的工具类 */
    private AgentSseResponseWriter() {
    }

    /**
     * 消费上游 SSE 行并在收到首行后提交响应
     *
     * <p>上游抛出异常时不获取响应写入器，让统一异常处理器保留原始错误状态
     *
     * @param upstream 接收行消费器并启动上游 SSE 转发的调用
     * @param response 待写入的 HTTP 响应
     * @throws IOException Servlet 响应写入失败时抛出
     */
    static void forward(Consumer<Consumer<String>> upstream, HttpServletResponse response) throws IOException {
        // Do not obtain the writer before the upstream call. RestTemplate maps
        // upstream errors to BizException; committing SSE first would hide them.
        final PrintWriter[] writerRef = new PrintWriter[1];
        upstream.accept(line -> {
            try {
                if (writerRef[0] == null) {
                    response.setContentType("text/event-stream");
                    response.setCharacterEncoding("UTF-8");
                    writerRef[0] = response.getWriter();
                }
                writerRef[0].write(line + "\n");
                writerRef[0].flush();
            } catch (IOException e) {
                throw new UncheckedIOException(e);
            }
        });
        if (writerRef[0] != null) {
            writerRef[0].close();
        }
    }
}
