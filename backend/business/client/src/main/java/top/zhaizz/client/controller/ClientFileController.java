package top.zhaizz.client.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import top.zhaizz.log.constant.OperationLogConstants;
import top.zhaizz.log.annotation.OperationLog;
import top.zhaizz.common.result.Result;
import top.zhaizz.infrastructure.storage.ImageCategory;
import top.zhaizz.infrastructure.storage.ImageStorageGateway;

/**
 * 用户图片上传入口
 */
@RestController
@RequestMapping("/api/client/files")
@RequiredArgsConstructor
public class ClientFileController {

    /** 图片存储网关 */
    private final ImageStorageGateway imageStorageGateway;

    /**
     * 上传当前用户的头像
     * @param file 待上传的图片文件
     * @return 包含已上传头像 URL 的成功响应
     */
    @OperationLog(action = OperationLogConstants.ACTION_FILE_UPLOAD, module = OperationLogConstants.MODULE_FILE)
    @PostMapping("/avatar")
    public Result<String> uploadAvatar(@RequestParam("file") MultipartFile file) {
        return Result.success(imageStorageGateway.upload(file, ImageCategory.AVATAR));
    }
}
