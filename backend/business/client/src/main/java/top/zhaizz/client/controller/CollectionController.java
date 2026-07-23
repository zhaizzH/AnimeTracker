package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.CollectionService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.util.SecurityUtil;
import top.zhaizz.pojo.dto.CollectionUpdateDTO;
import top.zhaizz.pojo.dto.EpStatusDTO;
import top.zhaizz.pojo.vo.UserCollectionVO;

/**
 * 收藏控制器
 */
@RestController
@RequestMapping("/api/user/collections")
@RequiredArgsConstructor
@Validated
public class CollectionController {

    private final CollectionService collectionService;

    /**
     * 获取当前登录用户收藏列表
     */
    @GetMapping
    public Result<PageResult<UserCollectionVO>> listCollections(
            @RequestParam(required = false) @Min(1) @Max(5) Integer type,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.listCollections(userId, type, page, size));
    }

    /**
     * 获取当前登录用户收藏详情
     */
    @GetMapping("/{subjectId}")
    public Result<UserCollectionVO> getCollection(@PathVariable Long subjectId) {
        Long userId = SecurityUtil.getCurrentUserId();
        UserCollectionVO vo = collectionService.getCollection(userId, subjectId);
        return vo != null ? Result.success(vo) : Result.success(null);
    }

    /**
     * 新增或修改收藏
     */
    @PutMapping("/{subjectId}")
    public Result<Void> saveOrUpdate(
            @PathVariable Long subjectId,
            @Valid @RequestBody CollectionUpdateDTO dto) {
        Long userId = SecurityUtil.getCurrentUserId();
        collectionService.saveOrUpdate(userId, subjectId, dto);
        return Result.success();
    }

    /**
     * 删除收藏
     */
    @DeleteMapping("/{subjectId}")
    public Result<Void> deleteCollection(@PathVariable Long subjectId) {
        Long userId = SecurityUtil.getCurrentUserId();
        collectionService.deleteCollection(userId, subjectId);
        return Result.success();
    }

    /**
     * 更新剧集进度
     */
    @PatchMapping("/{subjectId}/ep-status")
    public Result<Void> updateEpStatus(
            @PathVariable Long subjectId,
            @RequestBody @Valid EpStatusDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        collectionService.updateEpStatus(userId, subjectId, request.getEpStatus());
        return Result.success();
    }
}
