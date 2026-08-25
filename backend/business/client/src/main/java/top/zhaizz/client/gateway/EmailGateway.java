package top.zhaizz.client.gateway;

/** 邮件发送外部端口，不向业务层暴露供应商 SDK 类型。 */
public interface EmailGateway {
    void send(String recipient, String subject, String text);
}
