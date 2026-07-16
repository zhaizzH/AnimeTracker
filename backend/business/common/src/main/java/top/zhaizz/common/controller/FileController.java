package top.zhaizz.common.controller;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import top.zhaizz.common.config.MinioProperties;
import top.zhaizz.common.result.Result;

import java.util.List;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/common/files")
@RequiredArgsConstructor
public class FileController {

    private final MinioClient minioClient;
    private final MinioProperties minioProperties;

    private static final List<String> ALLOWED_CONTENT_TYPES = List.of("image/jpeg", "image/png", "image/webp");
    private static final List<String> ALLOWED_CATEGORIES = List.of("avatar", "cover");

    @PostMapping("/upload")
    public Result<String> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(defaultValue = "avatar") String type) {

        // 校验分类
        if (!ALLOWED_CATEGORIES.contains(type)) {
            return Result.error(400, "无效的上传分类: " + type);
        }

        // 校验文件类型
        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_CONTENT_TYPES.contains(contentType)) {
            return Result.error(400, "仅支持 JPG/PNG/WebP 格式的图片");
        }

        // 推断扩展名
        String ext = switch (contentType) {
            case "image/jpeg" -> "jpg";
            case "image/png" -> "png";
            case "image/webp" -> "webp";
            default -> throw new IllegalStateException("Unexpected content type: " + contentType);
        };

        // 生成对象路径
        String dir = type + "s"; // avatar → avatars, cover → covers
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

            log.info("File uploaded: {}", url);
            return Result.success(url);
        } catch (Exception e) {
            log.error("MinIO upload failed", e);
            return Result.error(500, "文件上传失败: " + e.getMessage());
        }
    }
}
