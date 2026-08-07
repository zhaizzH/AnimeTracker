package top.zhaizz.common.controller;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.config.MinioProperties;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.Result;

import java.util.List;
import java.util.UUID;

/**
 * 文件上传控制器：图片存 MinIO，返回可访问 URL
 */
@Slf4j
@RestController
@RequestMapping("/api/common/files")
@RequiredArgsConstructor
public class FileController {

    private final MinioClient minioClient;
    private final MinioProperties minioProperties;

    private static final List<String> ALLOWED_CONTENT_TYPES = List.of("image/jpeg", "image/png", "image/webp");
    private static final List<String> ALLOWED_CATEGORIES = List.of("avatar", "cover");

    /**
     * 上传图片到 MinIO 并返回访问 URL；type 限定 avatar/cover，仅接受 JPG/PNG/WebP
     */
    @PostMapping("/upload")
    public Result<String> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(defaultValue = "avatar") String type) {

        if (!ALLOWED_CATEGORIES.contains(type)) {
            throw new BizException(ErrorType.BAD_REQUEST, "无效的上传分类: " + type);
        }

        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_CONTENT_TYPES.contains(contentType)) {
            throw new BizException(ErrorType.BAD_REQUEST, "仅支持 JPG/PNG/WebP 格式的图片");
        }

        String ext = switch (contentType) {
            case "image/jpeg" -> "jpg";
            case "image/png" -> "png";
            case "image/webp" -> "webp";
            default -> throw new IllegalStateException("Unexpected content type: " + contentType);
        };

        // type 复数化拼对象路径：avatar → avatars, cover → covers
        String dir = type + "s";
        String objectName = dir + "/" + UUID.randomUUID() + "." + ext;

        try {
            minioClient.putObject(PutObjectArgs.builder()
                    .bucket(minioProperties.getBucket())
                    .object(objectName)
                    .stream(file.getInputStream(), file.getSize(), -1)
                    .contentType(contentType)
                    .build());

            String url = minioProperties.getEndpoint() + "/"
                    + minioProperties.getBucket() + "/"
                    + objectName;

            return Result.success(url);
        } catch (Exception e) {
            log.error("文件上传失败", e);
            throw new BizException(ErrorType.INTERNAL_ERROR, "文件上传失败");
        }
    }
}
