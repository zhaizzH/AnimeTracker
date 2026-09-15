package top.zhaizz.infrastructure.storage;

import org.springframework.web.multipart.MultipartFile;

/**
 * 图片对象存储边界
 */
public interface ImageStorageGateway {

    /**
     * 校验并上传指定分类的图片，返回可访问 URL
     * @param file 非 null 的图片文件，支持 JPEG、PNG、WebP MIME 类型
     * @param category 非 null 的目标存储分类
     * @return 上传后的公开访问 URL
     * @throws top.zhaizz.common.exception.BizException 类型不支持时为 BAD_REQUEST；上传失败时为 INTERNAL_ERROR
     */
    String upload(MultipartFile file, ImageCategory category);
}
