package top.zhaizz.infrastructure.email;

/** 邮件发送外部端口，不向业务层暴露供应商 SDK 类型。 */
public interface EmailGateway {
    /**
     * 发送业务方提供的纯文本邮件。
     * @param recipient 接收邮件的地址
     * @param subject 邮件主题
     * @param text 邮件纯文本正文
     * @throws IllegalStateException 供应商发送失败时抛出，调用方负责业务错误处理
     */
    void send(String recipient, String subject, String text);
}
