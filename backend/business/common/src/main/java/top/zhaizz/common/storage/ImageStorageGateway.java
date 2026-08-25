package top.zhaizz.common.storage;

import org.springframework.web.multipart.MultipartFile;

/**
 * 图片对象存储边界
 */
public interface ImageStorageGateway {

    /**
     * 校验并上传指定分类的图片，返回可访问 URL
     */
    String upload(MultipartFile file, ImageCategory category);
}
