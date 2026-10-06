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
            return publicUrl(objectName);
        } catch (Exception exception) {
            log.error("文件上传失败", exception);
            throw new BizException(ErrorType.INTERNAL_ERROR, "文件上传失败");
        }
    }

    /**
     * 生成图片对外访问地址
     * <p>前缀语义与导入器一致：前缀已指向桶根，故不再重复拼接桶名；
     * 未配置时退回 SDK 端点 + 桶名，仅适用于 SDK 与浏览器同机
     *
     * @param objectName 桶内对象路径
     * @return 可直接给浏览器的图片地址
     */
    private String publicUrl(String objectName) {
        String baseUrl = minioProperties.getPublicBaseUrl();
        if (baseUrl != null && !baseUrl.isBlank()) {
            return stripTrailingSlash(baseUrl) + "/" + objectName;
        }
        return stripTrailingSlash(minioProperties.getEndpoint()) + "/" + minioProperties.getBucket() + "/" + objectName;
    }

    /**
     * 去掉末尾斜杠，避免拼接出双斜杠
     * @param value 待处理字符串
     * @return 去除尾部 {@code /} 的结果；输入为 {@code null} 时原样返回
     */
    private static String stripTrailingSlash(String value) {
        return value == null ? null : value.replaceAll("/+$", "");
    }
}
