package top.zhaizz.infrastructure.storage.minio;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.infrastructure.storage.ImageCategory;
import top.zhaizz.infrastructure.storage.ImageStorageGateway;

import java.util.Map;
import java.util.UUID;

/**
 * 基于 MinIO 的图片存储实现
 */
@Component
public class MinioImageStorageGateway implements ImageStorageGateway {

    /** 当前类的日志记录器 */
    private static final Logger log = LoggerFactory.getLogger(MinioImageStorageGateway.class);
    /** 允许上传的 MIME 类型及其服务端文件后缀 */
    private static final Map<String, String> EXTENSIONS = Map.of(
            "image/jpeg", "jpg",
            "image/png", "png",
            "image/webp", "webp");

    /** 执行对象上传的 SDK 客户端 */
    private final MinioClient minioClient;
    /** 用于选择存储桶及生成访问地址的配置 */
    private final MinioProperties minioProperties;

    /**
     * 创建 MinIO 图片存储实现
     *
     * @param minioClient 执行对象上传的 SDK 客户端
     * @param minioProperties 用于选择存储桶及生成访问地址的配置
     */
    public MinioImageStorageGateway(MinioClient minioClient, MinioProperties minioProperties) {
        this.minioClient = minioClient;
        this.minioProperties = minioProperties;
    }

    /**
     * {@inheritDoc}
     * <p>对象名使用服务端 UUID，不使用客户端文件名
     */
    @Override
    public String upload(MultipartFile file, ImageCategory category) {
        String contentType = file.getContentType();
        String extension = contentType == null ? null : EXTENSIONS.get(contentType);
        if (extension == null) {
            throw new BizException(ErrorType.BAD_REQUEST, "仅支持 JPG/PNG/WebP 格式的图片");
        }

        String objectName = category.getDirectory() + "/" + UUID.randomUUID() + "." + extension;
        try {
            minioClient.putObject(PutObjectArgs.builder()
                    .bucket(minioProperties.getBucket())
                    .object(objectName)
                    .stream(file.getInputStream(), file.getSize(), -1)
                    .contentType(contentType)
                    .build());
            return minioProperties.getEndpoint() + "/" + minioProperties.getBucket() + "/" + objectName;
        } catch (Exception exception) {
            log.error("文件上传失败", exception);
            throw new BizException(ErrorType.INTERNAL_ERROR, "文件上传失败");
        }
    }
}
