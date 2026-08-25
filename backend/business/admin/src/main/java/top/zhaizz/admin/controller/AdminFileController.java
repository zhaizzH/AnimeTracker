package top.zhaizz.admin.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.storage.ImageCategory;
import top.zhaizz.common.storage.ImageStorageGateway;

/**
 * 管理端图片上传入口
 */
@RestController
@RequestMapping("/api/admin/files")
@RequiredArgsConstructor
public class AdminFileController {

    private final ImageStorageGateway imageStorageGateway;

    /**
     * 上传番剧封面
     */
    @OperationLog(action = OperationLogConstants.ACTION_FILE_UPLOAD, module = OperationLogConstants.MODULE_FILE)
    @PostMapping("/cover")
    public Result<String> uploadCover(@RequestParam("file") MultipartFile file) {
        return Result.success(imageStorageGateway.upload(file, ImageCategory.COVER));
    }
}
