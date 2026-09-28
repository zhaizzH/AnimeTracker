package top.zhaizz.app.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * LLM Agent 服务连接配置
 */
@ConfigurationProperties(prefix = "at.agent")
public class AgentProperties {
    /** Agent 服务地址 */
    private String baseUrl;
    /** 连接超时（毫秒） */
    private long connectTimeout = 10_000;
    /** 普通请求读超时（毫秒） */
    private long readTimeout = 30_000;

    /** 创建使用字段默认值的配置对象，供 Spring 属性绑定使用 */
    public AgentProperties() {
    }

    /**
     * 获取 Agent 服务地址
     * @return Python Agent 服务的基础地址；未配置时为 {@code null}
     */
    public String getBaseUrl() {
        return this.baseUrl;
    }

    /**
     * 获取连接超时毫秒数
     * @return 建立连接允许的最长等待时间，默认 10000 毫秒
     */
    public long getConnectTimeout() {
        return this.connectTimeout;
    }

    /**
     * 获取普通请求读超时毫秒数
     * @return 读取响应允许的最长等待时间，默认 30000 毫秒
     */
    public long getReadTimeout() {
        return this.readTimeout;
    }

    /**
     * 替换 Agent 服务地址
     * @param baseUrl Python Agent 服务的基础地址，可为 {@code null}
     */
    public void setBaseUrl(final String baseUrl) {
        this.baseUrl = baseUrl;
    }

    /**
     * 替换连接超时毫秒数
     * @param connectTimeout 建立连接的最长等待时间，单位毫秒
     */
    public void setConnectTimeout(final long connectTimeout) {
        this.connectTimeout = connectTimeout;
    }

    /**
     * 替换普通请求读超时毫秒数
     * @param readTimeout 读取响应的最长等待时间，单位毫秒
     */
    public void setReadTimeout(final long readTimeout) {
        this.readTimeout = readTimeout;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof AgentProperties)) return false;
        final AgentProperties other = (AgentProperties) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getConnectTimeout() != other.getConnectTimeout()) return false;
        if (this.getReadTimeout() != other.getReadTimeout()) return false;
        final Object thisBaseUrl = this.getBaseUrl();
        final Object otherBaseUrl = other.getBaseUrl();
        if (thisBaseUrl == null ? otherBaseUrl != null : !thisBaseUrl.equals(otherBaseUrl)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof AgentProperties;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashConnectTimeout = this.getConnectTimeout();
        result = result * PRIME + (int) (hashConnectTimeout >>> 32 ^ hashConnectTimeout);
        final long hashReadTimeout = this.getReadTimeout();
        result = result * PRIME + (int) (hashReadTimeout >>> 32 ^ hashReadTimeout);
        final Object hashBaseUrl = this.getBaseUrl();
        result = result * PRIME + (hashBaseUrl == null ? 43 : hashBaseUrl.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "AgentProperties(baseUrl=" + this.getBaseUrl() + ", connectTimeout=" + this.getConnectTimeout() + ", readTimeout=" + this.getReadTimeout() + ")";
    }
}
