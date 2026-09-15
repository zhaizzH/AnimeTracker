package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.CollectionService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.auth.util.SecurityUtil;
import top.zhaizz.pojo.dto.collection.CollectionQueryDTO;
import top.zhaizz.pojo.dto.collection.CollectionUpdateDTO;
import top.zhaizz.pojo.dto.collection.EpisodeStatusDTO;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.vo.collection.UserCollectionVO;
import top.zhaizz.pojo.vo.collection.WishlistAddResultVO;

import java.util.Map;

/**
 * 追番控制器
 */
@RestController
@RequestMapping("/api/client/collections")
@RequiredArgsConstructor
public class CollectionController {

    /** 用户收藏业务服务 */
    private final CollectionService collectionService;

    /**
     * 获取当前登录用户收藏列表
     * @param request 收藏状态筛选与分页条件
     * @return 统一成功响应，其数据为：指定用户的收藏分页，包含条目信息
     */
    @GetMapping
    public Result<PageResult<UserCollectionVO>> listCollections(@Valid CollectionQueryDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.listCollections(userId, request));
    }

    /**
     * 获取当前登录用户收藏统计（key=type 1-5，value=数量）
     * @return 统一成功响应，其数据为：实际出现的收藏状态到数量的映射，缺失状态不补零
     */
    @GetMapping("/counts")
    public Result<Map<Integer, Long>> listCounts() {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.listCounts(userId));
    }

    /**
     * 获取当前登录用户收藏详情
     * @param subjectId 条目 ID
     * @return 统一成功响应，其数据为：用户收藏详情，未收藏时返回 {@code null}
     */
    @GetMapping("/{subjectId}")
    public Result<UserCollectionVO> getCollection(@PathVariable Long subjectId) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.getCollection(userId, subjectId));
    }

    /**
     * 新增或修改收藏
     * @param subjectId 条目 ID
     * @param request 收藏类型与可选评分、进度
     * @return 无数据的统一成功响应
     */
    @PostMapping("/{subjectId}/save")
    public Result<Void> saveOrUpdate(
            @PathVariable Long subjectId,
            @Valid @RequestBody CollectionUpdateDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        collectionService.saveOrUpdate(userId, subjectId, request);
        return Result.success();
    }

    /**
     * 仅当未收藏时加入想看（幂等，不覆盖已有收藏）
     * @param subjectId 条目 ID
     * @return 包含新增或已有收藏状态的成功响应
     */
    @PostMapping("/{subjectId}/wishlist")
    public Result<WishlistAddResultVO> addToWishlist(@PathVariable Long subjectId) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.addToWishlistIfAbsent(userId, subjectId));
    }

    /**
     * 删除收藏
     * @param subjectId 条目 ID
     * @return 无数据的统一成功响应
     */
    @PostMapping("/{subjectId}/remove")
    public Result<Void> deleteCollection(@PathVariable Long subjectId) {
        Long userId = SecurityUtil.getCurrentUserId();
        collectionService.deleteCollection(userId, subjectId);
        return Result.success();
    }

    /**
     * 登录用户每周追番列表
     * @param request 年份、季度、星期及分页条件
     * @return 统一成功响应，其数据为：符合日程条件的分页结果
     */
    @GetMapping("/schedule")
    public Result<PageResult<UserCollectionVO>> listSchedule(@Valid ScheduleQueryDTO request) {
        Long userId = SecurityUtil.getCurrentUserId();
        return Result.success(collectionService.listSchedule(userId, request));
    }

    /**
     * 更新剧集进度
     * @param subjectId 条目 ID
     * @param request 目标已看集数
     * @return 无数据的统一成功响应
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
