package top.zhaizz.app.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

/**
 * CORS 跨域白名单配置（生产只允许 AT_CORS_ALLOWED_ORIGINS 中的明确来源，禁止通配符）
 */
@ConfigurationProperties(prefix = "at.cors")
public class CorsProperties {
    /** 允许跨域请求的 Origin 白名单 */
    private List<String> allowedOrigins;

    /** 创建无白名单的配置对象 */
    public CorsProperties() {
    }

    /**
     * 获取允许跨域请求的 Origin 白名单
     * @return 允许的来源列表；未配置时为 {@code null}
     */
    public List<String> getAllowedOrigins() {
        return this.allowedOrigins;
    }

    /**
     * 替换允许跨域请求的 Origin 白名单
     * @param allowedOrigins 允许的来源列表，可为 {@code null}；保存传入列表引用
     */
    public void setAllowedOrigins(final List<String> allowedOrigins) {
        this.allowedOrigins = allowedOrigins;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CorsProperties)) return false;
        final CorsProperties other = (CorsProperties) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisAllowedOrigins = this.getAllowedOrigins();
        final Object otherAllowedOrigins = other.getAllowedOrigins();
        if (thisAllowedOrigins == null ? otherAllowedOrigins != null : !thisAllowedOrigins.equals(otherAllowedOrigins)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CorsProperties;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashAllowedOrigins = this.getAllowedOrigins();
        result = result * PRIME + (hashAllowedOrigins == null ? 43 : hashAllowedOrigins.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CorsProperties(allowedOrigins=" + this.getAllowedOrigins() + ")";
    }
}
