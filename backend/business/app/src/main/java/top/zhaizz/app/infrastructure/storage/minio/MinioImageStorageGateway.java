package top.zhaizz.app.infrastructure.storage.minio;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.storage.ImageCategory;
import top.zhaizz.common.storage.ImageStorageGateway;

import java.util.Map;
import java.util.UUID;

/**
 * 基于 MinIO 的图片存储实现
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class MinioImageStorageGateway implements ImageStorageGateway {

    private static final Map<String, String> EXTENSIONS = Map.of(
            "image/jpeg", "jpg",
            "image/png", "png",
            "image/webp", "webp");

    private final MinioClient minioClient;
    private final MinioProperties minioProperties;

    /**
     * 使用服务端 UUID 对象名上传 JPG、PNG 或 WebP 图片
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
