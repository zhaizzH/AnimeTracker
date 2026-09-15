package top.zhaizz.infrastructure.storage.minio;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * MinIO 对象存储配置属性
 */
@Data
@ConfigurationProperties(prefix = "minio")
public class MinioProperties {
    /** MinIO HTTP 服务地址，同时用作上传后访问 URL 前缀 */
    private String endpoint;
    /** MinIO 访问标识，来自 minio.access-key 配置 */
    private String accessKey;
    /** MinIO 访问密钥，仅供 SDK 认证，禁止日志输出 */
    private String secretKey;
    /** 上传目标存储桶名称，来自 minio.bucket 配置 */
    private String bucket;
}
