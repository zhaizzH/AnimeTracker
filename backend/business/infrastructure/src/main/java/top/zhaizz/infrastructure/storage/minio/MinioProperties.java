package top.zhaizz.infrastructure.storage.minio;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * MinIO 对象存储配置属性
 */
@ConfigurationProperties(prefix = "minio")
public class MinioProperties {
    /** MinIO HTTP 服务地址，供 SDK 连接使用，不得作为对外访问 URL 前缀 */
    private String endpoint;
    /** 图片对外访问前缀（反向代理地址）；为空时退回 endpoint 拼接，仅适用于同机访问 */
    private String publicBaseUrl;
    /** MinIO 访问标识，来自 minio.access-key 配置 */
    private String accessKey;
    /** MinIO 访问密钥，仅供 SDK 认证，禁止日志输出 */
    private String secretKey;
    /** 上传目标存储桶名称，来自 minio.bucket 配置 */
    private String bucket;

    /** 创建全部字段为空的配置对象，供 Spring 属性绑定使用 */
    public MinioProperties() {
    }

    /**
     * 获取 MinIO 对外访问前缀
     * @return 反向代理前缀；未配置时为 {@code null}
     */
    public String getPublicBaseUrl() {
        return this.publicBaseUrl;
    }

    /**
     * 替换 MinIO 对外访问前缀
     * @param publicBaseUrl 反向代理前缀，可为 {@code null}
     */
    public void setPublicBaseUrl(final String publicBaseUrl) {
        this.publicBaseUrl = publicBaseUrl;
    }

    /**
     * 获取 MinIO HTTP 服务地址
     * @return 对象存储访问地址；未配置时为 {@code null}
     */
    public String getEndpoint() {
        return this.endpoint;
    }

    /**
     * 获取 MinIO 访问标识
     * @return SDK 认证使用的 access key；未配置时为 {@code null}
     */
    public String getAccessKey() {
        return this.accessKey;
    }

    /**
     * 获取 MinIO 访问密钥
     * @return SDK 认证使用的 secret key，禁止日志输出；未配置时为 {@code null}
     */
    public String getSecretKey() {
        return this.secretKey;
    }

    /**
     * 获取上传目标存储桶名称
     * @return 对象上传的目标桶；未配置时为 {@code null}
     */
    public String getBucket() {
        return this.bucket;
    }

    /**
     * 替换 MinIO HTTP 服务地址
     * @param endpoint 对象存储访问地址，可为 {@code null}
     */
    public void setEndpoint(final String endpoint) {
        this.endpoint = endpoint;
    }

    /**
     * 替换 MinIO 访问标识
     * @param accessKey SDK 认证使用的 access key，可为 {@code null}
     */
    public void setAccessKey(final String accessKey) {
        this.accessKey = accessKey;
    }

    /**
     * 替换 MinIO 访问密钥
     * @param secretKey SDK 认证使用的 secret key，可为 {@code null}
     */
    public void setSecretKey(final String secretKey) {
        this.secretKey = secretKey;
    }

    /**
     * 替换上传目标存储桶名称
     * @param bucket 对象上传的目标桶，可为 {@code null}
     */
    public void setBucket(final String bucket) {
        this.bucket = bucket;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof MinioProperties)) return false;
        final MinioProperties other = (MinioProperties) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisEndpoint = this.getEndpoint();
        final Object otherEndpoint = other.getEndpoint();
        if (thisEndpoint == null ? otherEndpoint != null : !thisEndpoint.equals(otherEndpoint)) return false;
        final Object thisPublicBaseUrl = this.getPublicBaseUrl();
        final Object otherPublicBaseUrl = other.getPublicBaseUrl();
        if (thisPublicBaseUrl == null ? otherPublicBaseUrl != null : !thisPublicBaseUrl.equals(otherPublicBaseUrl)) return false;
        final Object thisAccessKey = this.getAccessKey();
        final Object otherAccessKey = other.getAccessKey();
        if (thisAccessKey == null ? otherAccessKey != null : !thisAccessKey.equals(otherAccessKey)) return false;
        final Object thisSecretKey = this.getSecretKey();
        final Object otherSecretKey = other.getSecretKey();
        if (thisSecretKey == null ? otherSecretKey != null : !thisSecretKey.equals(otherSecretKey)) return false;
        final Object thisBucket = this.getBucket();
        final Object otherBucket = other.getBucket();
        if (thisBucket == null ? otherBucket != null : !thisBucket.equals(otherBucket)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof MinioProperties;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashEndpoint = this.getEndpoint();
        result = result * PRIME + (hashEndpoint == null ? 43 : hashEndpoint.hashCode());
        final Object hashPublicBaseUrl = this.getPublicBaseUrl();
        result = result * PRIME + (hashPublicBaseUrl == null ? 43 : hashPublicBaseUrl.hashCode());
        final Object hashAccessKey = this.getAccessKey();
        result = result * PRIME + (hashAccessKey == null ? 43 : hashAccessKey.hashCode());
        final Object hashSecretKey = this.getSecretKey();
        result = result * PRIME + (hashSecretKey == null ? 43 : hashSecretKey.hashCode());
        final Object hashBucket = this.getBucket();
        result = result * PRIME + (hashBucket == null ? 43 : hashBucket.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "MinioProperties(endpoint=" + this.getEndpoint() + ", publicBaseUrl=" + this.getPublicBaseUrl() + ", accessKey=" + this.getAccessKey() + ", secretKey=" + this.getSecretKey() + ", bucket=" + this.getBucket() + ")";
    }
}
