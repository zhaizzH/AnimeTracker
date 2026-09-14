package top.zhaizz.infrastructure.email.resend;

import com.resend.Resend;
import com.resend.core.exception.ResendException;
import com.resend.services.emails.model.CreateEmailOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import top.zhaizz.infrastructure.email.EmailGateway;

/** 使用 Resend SDK 发送业务层提供的邮件内容。 */
@Component
public class ResendEmailGateway implements EmailGateway {
    /** 用于提交邮件的供应商客户端。 */
    private final Resend resend;
    /** resend.send-email 配置的发件地址。 */
    private final String sender;

    /**
     * 绑定发送客户端和配置的发件人。
     * @param resend Resend SDK 客户端
     * @param sender 已配置的发件地址
     */
    public ResendEmailGateway(Resend resend,
                              @Value("${resend.send-email}") String sender) {
        this.resend = resend;
        this.sender = sender;
    }

    /** {@inheritDoc} */
    @Override
    public void send(String recipient, String subject, String text) {
        CreateEmailOptions request = CreateEmailOptions.builder()
                .from(sender)
                .to(recipient)
                .subject(subject)
                .text(text)
                .build();
        try {
            resend.emails().send(request);
        } catch (ResendException exception) {
            throw new IllegalStateException("Resend 邮件发送失败", exception);
        }
    }
}
