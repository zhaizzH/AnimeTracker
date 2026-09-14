package top.zhaizz.client.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import top.zhaizz.client.service.CollectionProgressService;
import top.zhaizz.common.result.Result;
import top.zhaizz.auth.util.SecurityUtil;
import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;

/**
 * 本周追番进度预览控制器。
 */
@RestController
@RequestMapping("/api/client/collections")
@RequiredArgsConstructor
public class CollectionProgressController {

    /** 收藏进度业务服务。 */
    private final CollectionProgressService collectionProgressService;

    /**
     * 生成当前登录用户本周追番进度预览。
     * @return 统一成功响应，其数据为：生成当前登录用户本周追番进度预览
     */
    @PostMapping("/progress-preview")
    public Result<CollectionProgressPreviewVO> createProgressPreview() {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionProgressService.createPreview(userId));
    }

    /**
     * 确认执行预览：重新校验，数据变化返回 PREVIEW_CHANGED，否则逐项执行并汇总。
     * @param previewId 已生成的进度预览标识
     * @return 统一成功响应，其数据为：确认执行预览：重新校验，数据变化返回 PREVIEW_CHANGED，否则逐项执行并汇总
     */
    @PostMapping("/progress-preview/{previewId}/execute")
    public Result<CollectionProgressExecutionVO> executeProgressPreview(@PathVariable String previewId) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionProgressService.executePreview(userId, previewId));
    }
}
