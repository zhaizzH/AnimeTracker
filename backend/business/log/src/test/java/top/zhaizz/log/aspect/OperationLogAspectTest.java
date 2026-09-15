package top.zhaizz.log.aspect;

import org.aspectj.lang.ProceedingJoinPoint;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import org.springframework.web.servlet.HandlerMapping;
import top.zhaizz.log.annotation.OperationLog;
import top.zhaizz.log.mapper.OperationLogMapper;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证日志旁路失败隔离和敏感请求数据不采集 */
class OperationLogAspectTest {
    /** 清除测试线程的请求上下文，避免污染其他测试 */
    @AfterEach
    void clearRequest() { RequestContextHolder.resetRequestAttributes(); }

    /**
     * 验证匿名请求成功且日志库失败时，原始返回对象保持不变
     * @throws Throwable 模拟调用意外失败时向测试框架传播
     */
    @Test
    void writeFailureKeepsSuccessfulResult() throws Throwable {
        OperationLogMapper mapper = mock(OperationLogMapper.class);
        doThrow(new IllegalStateException("secret-sql")).when(mapper).insert(any(top.zhaizz.pojo.entity.OperationLog.class));
        ProceedingJoinPoint call = mock(ProceedingJoinPoint.class);
        Object result = new Object();
        when(call.proceed()).thenReturn(result);
        assertSame(result, new OperationLogAspect(mapper).around(call, annotation()));
        verify(mapper, times(1)).insert(any(top.zhaizz.pojo.entity.OperationLog.class));
    }

    /**
     * 验证日志落库失败不会替换业务异常
     * @throws Throwable 配置模拟调用意外失败时向测试框架传播
     */
    @Test
    void writeFailureKeepsOriginalException() throws Throwable {
        OperationLogMapper mapper = mock(OperationLogMapper.class);
        doThrow(new IllegalStateException("database-secret")).when(mapper).insert(any(top.zhaizz.pojo.entity.OperationLog.class));
        ProceedingJoinPoint call = mock(ProceedingJoinPoint.class);
        RuntimeException failure = new RuntimeException("token-secret");
        when(call.proceed()).thenThrow(failure);
        assertSame(failure, assertThrows(RuntimeException.class,
                () -> new OperationLogAspect(mapper).around(call, annotation())));
    }

    /**
     * 验证失败状态及匿名身份，并确保原始参数、请求路径和异常消息不落库
     * @throws Throwable 配置模拟调用意外失败时向测试框架传播
     */
    @Test
    void recordsOnlySafeFailureMetadata() throws Throwable {
        OperationLogMapper mapper = mock(OperationLogMapper.class);
        ProceedingJoinPoint call = mock(ProceedingJoinPoint.class);
        when(call.proceed()).thenThrow(new IllegalArgumentException("password=secret"));
        MockHttpServletRequest request = new MockHttpServletRequest("POST", "/users/private-input");
        request.setAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE, "/users/{id}");
        request.addHeader("User-Agent", "private-input");
        RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(request));
        assertThrows(IllegalArgumentException.class,
                () -> new OperationLogAspect(mapper).around(call, annotation()));
        ArgumentCaptor<top.zhaizz.pojo.entity.OperationLog> capture = ArgumentCaptor.forClass(top.zhaizz.pojo.entity.OperationLog.class);
        verify(mapper).insert(capture.capture());
        var entity = capture.getValue();
        assertEquals(1, entity.getStatus());
        assertEquals("IllegalArgumentException", entity.getErrorMsg());
        assertEquals("/users/{id}", entity.getPath());
        assertNull(entity.getUserId());
        assertNull(entity.getParams());
        assertNull(entity.getUsername());
        assertNull(entity.getUserAgent());
        verify(call, never()).getArgs();
    }

    /**
     * 创建稳定的测试动作注解
     * @return 表示管理员导入操作的注解桩
     */
    private OperationLog annotation() {
        OperationLog annotation = mock(OperationLog.class);
        when(annotation.action()).thenReturn("IMPORT_RUN");
        when(annotation.module()).thenReturn("IMPORT");
        return annotation;
    }
}
