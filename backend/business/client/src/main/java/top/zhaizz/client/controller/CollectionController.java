package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.CollectionService;
import top.zhaizz.client.util.SeasonUtil;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.util.SecurityUtil;
import top.zhaizz.pojo.dto.collection.CollectionQueryDTO;
import top.zhaizz.pojo.dto.collection.CollectionUpdateDTO;
import top.zhaizz.pojo.dto.collection.EpisodeStatusDTO;
import top.zhaizz.pojo.vo.collection.UserCollectionVO;

import java.util.Map;

/**
 * 追番控制器
 */
@RestController
@RequestMapping("/api/client/collections")
@RequiredArgsConstructor
@Validated
public class CollectionController {

    private final CollectionService collectionService;

    /**
     * 获取当前登录用户收藏列表
     */
    @GetMapping
    public Result<PageResult<UserCollectionVO>> listCollections(@Valid CollectionQueryDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.listCollections(userId, request));
    }

    /**
     * 获取当前登录用户收藏统计（key=type 1-5，value=数量）
     */
    @GetMapping("/counts")
    public Result<Map<Integer, Long>> listCounts() {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.listCounts(userId));
    }

    /**
     * 获取当前登录用户收藏详情
     */
    @GetMapping("/{subjectId}")
    public Result<UserCollectionVO> getCollection(@PathVariable Long subjectId) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.getCollection(userId, subjectId));
    }

    /**
     * 新增或修改收藏
     */
    @PostMapping("/{subjectId}/save")
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
    @PostMapping("/{subjectId}/remove")
    public Result<Void> deleteCollection(@PathVariable Long subjectId) {
        Long userId = SecurityUtil.getCurrentUserId();
        collectionService.deleteCollection(userId, subjectId);
        return Result.success();
    }

    /**
     * 登录用户每周追番列表
     */
    @GetMapping("/schedule")
    public Result<PageResult<UserCollectionVO>> listSchedule(
            @RequestParam(defaultValue = "-1") @Min(-1) @Max(6) int weekday,
            @RequestParam(required = false) @Min(1970) @Max(2100) Integer year,
            @RequestParam(required = false) @Pattern(regexp = "spring|summer|autumn|winter", message = "季度仅允许: spring/summer/autumn/winter") String quarter,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "50") @Min(1) @Max(100) int size) {
        Long userId = SecurityUtil.getCurrentUserId();
        int y = year != null ? year : SeasonUtil.getCurrentYear();
        String q = quarter != null ? quarter : SeasonUtil.getCurrentQuarter();
        Integer wd = weekday == -1 ? null : weekday;
        return Result.success(collectionService.listSchedule(userId, y, q, wd, page, size));
    }

    /**
     * 更新剧集进度
     */
    @PostMapping("/{subjectId}/ep-status")
    public Result<Void> updateEpStatus(
            @PathVariable Long subjectId,
            @RequestBody @Valid EpisodeStatusDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        collectionService.updateEpStatus(userId, subjectId, request.getEpStatus());
        return Result.success();
    }
}
