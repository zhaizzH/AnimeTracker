package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.CollectionService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.CollectionUpdateDTO;
import top.zhaizz.pojo.vo.UserCollectionVO;

@RestController
@RequestMapping("/api/user/collections")
@RequiredArgsConstructor
@Validated
public class CollectionController {

    private final CollectionService collectionService;

    @GetMapping
    public Result<PageResult<UserCollectionVO>> listCollections(
            @RequestParam(required = false) @Min(1) @Max(5) Integer type,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        Long userId = getCurrentUserId();
        return Result.success(collectionService.listCollections(userId, type, page, size));
    }

    @GetMapping("/{subjectId}")
    public Result<UserCollectionVO> getCollection(@PathVariable Long subjectId) {
        Long userId = getCurrentUserId();
        UserCollectionVO vo = collectionService.getCollection(userId, subjectId);
        return vo != null ? Result.success(vo) : Result.success(null);
    }

    @PutMapping("/{subjectId}")
    public Result<Void> saveOrUpdate(
            @PathVariable Long subjectId,
            @Valid @RequestBody CollectionUpdateDTO dto) {
        Long userId = getCurrentUserId();
        collectionService.saveOrUpdate(userId, subjectId, dto);
        return Result.success();
    }

    @DeleteMapping("/{subjectId}")
    public Result<Void> deleteCollection(@PathVariable Long subjectId) {
        Long userId = getCurrentUserId();
        collectionService.deleteCollection(userId, subjectId);
        return Result.success();
    }

    @PatchMapping("/{subjectId}/ep-status")
    public Result<Void> updateEpStatus(
            @PathVariable Long subjectId,
            @RequestBody @Valid EpStatusRequest request) {
        Long userId = getCurrentUserId();
        collectionService.updateEpStatus(userId, subjectId, request.getEpStatus());
        return Result.success();
    }

    @Data
    public static class EpStatusRequest {
        @Min(value = 0, message = "剧集进度不能为负")
        private int epStatus;
    }

    private Long getCurrentUserId() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return (Long) auth.getPrincipal();
    }
}
