package top.zhaizz.infrastructure;

import com.resend.Resend;
import com.resend.core.exception.ResendException;
import com.resend.services.emails.model.CreateEmailOptions;
import org.junit.jupiter.api.Test;
import top.zhaizz.infrastructure.email.resend.ResendEmailGateway;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 验证邮件适配器提交请求并保留供应商失败语义 */
class ResendGatewayTest {
    /** 业务提供的邮件正常提交给 SDK，不连接真实邮件服务 */
    @Test
    void submitsEmail() throws Exception {
        Resend resend = mock(Resend.class, RETURNS_DEEP_STUBS);
        var gateway = new ResendEmailGateway(resend, "sender@example.test");
        gateway.send("recipient@example.test", "测试主题", "测试正文");
        verify(resend.emails()).send(any(CreateEmailOptions.class));
    }

    /** SDK 失败保留原因并转为调用方可处理的非法状态异常 */
    @Test
    void mapsProviderFailure() throws Exception {
        Resend resend = mock(Resend.class, RETURNS_DEEP_STUBS);
        ResendException failure = mock(ResendException.class);
        when(resend.emails().send(any(CreateEmailOptions.class))).thenThrow(failure);
        var gateway = new ResendEmailGateway(resend, "sender@example.test");
        IllegalStateException error = assertThrows(IllegalStateException.class,
                () -> gateway.send("recipient@example.test", "主题", "正文"));
        assertEquals("Resend 邮件发送失败", error.getMessage());
        assertSame(failure, error.getCause());
    }
}
