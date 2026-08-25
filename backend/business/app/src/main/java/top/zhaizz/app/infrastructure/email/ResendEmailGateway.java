package top.zhaizz.app.infrastructure.email;

import com.resend.Resend;
import com.resend.core.exception.ResendException;
import com.resend.services.emails.model.CreateEmailOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import top.zhaizz.client.gateway.EmailGateway;

/** 使用 Resend SDK 发送业务层提供的邮件内容。 */
@Component
public class ResendEmailGateway implements EmailGateway {
    private final Resend resend;
    private final String sender;

    public ResendEmailGateway(Resend resend,
                              @Value("${resend.send-email}") String sender) {
        this.resend = resend;
        this.sender = sender;
    }

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
