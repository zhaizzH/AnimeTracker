package top.zhaizz.infrastructure.storage.minio;

import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.SetBucketPolicyArgs;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * MinIO 客户端配置与桶自动初始化
 * <p>启动时自动检查并创建 Bucket，设置公开读策略</p>
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
@EnableConfigurationProperties(MinioProperties.class)
public class MinioConfig {

    /** MinIO 连接与目标存储桶配置 */
    private final MinioProperties properties;

    /**
     * 按配置创建 MinIO 客户端
     * @return 使用配置端点和凭据的客户端
     */
    @Bean
    public MinioClient minioClient() {
        return MinioClient.builder()
                .endpoint(properties.getEndpoint())
                .credentials(properties.getAccessKey(), properties.getSecretKey())
                .build();
    }

    /**
     * 检查存储桶，仅对新建桶设置公开读策略；失败不阻断启动
     * @param minioClient 用于检查和初始化的客户端
     * @return 存储桶存在或初始化成功时为 true，出现异常时为 false
     */
    @Bean
    public boolean initMinioBucket(MinioClient minioClient) {
        try {
            boolean exists = minioClient.bucketExists(
                    BucketExistsArgs.builder().bucket(properties.getBucket()).build());
            if (!exists) {
                minioClient.makeBucket(
                        MakeBucketArgs.builder().bucket(properties.getBucket()).build());

                // 设置公开读策略
                String policy = """
                {
                  "Version": "2012-10-17",
                  "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": ["arn:aws:s3:::%s/*"]
                  }]
                }
                """.formatted(properties.getBucket());

                minioClient.setBucketPolicy(
                        SetBucketPolicyArgs.builder()
                                .bucket(properties.getBucket())
                                .config(policy)
                                .build());

                log.info("MinIO bucket '{}' created with public-read policy", properties.getBucket());
            } else {
                log.info("MinIO bucket '{}' already exists", properties.getBucket());
            }
            return true;
        } catch (Exception e) {
            log.warn("MinIO bucket init skipped (MinIO may not be running yet): {}", e.getMessage());
            return false;
        }
    }
}
