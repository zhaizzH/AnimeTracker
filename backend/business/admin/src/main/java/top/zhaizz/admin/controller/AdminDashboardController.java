package top.zhaizz.admin.controller;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import top.zhaizz.admin.service.DashboardService;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.vo.collection.CollectionStatsVO;
import top.zhaizz.pojo.vo.DashboardOverviewVO;
import top.zhaizz.pojo.vo.subject.HotSubjectVO;
import top.zhaizz.pojo.vo.subject.SubjectStatsVO;
import top.zhaizz.pojo.vo.TrendPointVO;

import java.util.List;

/**
 * 运营看板控制器
 */
@RestController
@RequestMapping("/api/admin/dashboard")
@RequiredArgsConstructor
@Validated
public class AdminDashboardController {

    private final DashboardService dashboardService;

    /**
     * 看板总览，管理后台进入看板页时加载核心运营指标
     */
    @GetMapping("/overview")
    public Result<DashboardOverviewVO> overview() {
        return Result.success(dashboardService.overview());
    }

    /**
     * 每日趋势（新增用户/收藏/登录），看板趋势图展示时触发
     */
    @GetMapping("/trends")
    public Result<List<TrendPointVO>> trends(
            @RequestParam(defaultValue = "30") @Min(1) @Max(90) int days) {
        return Result.success(dashboardService.trends(days));
    }

    /**
     * 收藏类型与评分分布，看板分布图加载时触发
     */
    @GetMapping("/collection-stats")
    public Result<CollectionStatsVO> collectionStats() {
        return Result.success(dashboardService.collectionStats());
    }

    /**
     * 番剧季度数量、导入状态与导入记录统计，看板内容面板加载时触发
     */
    @GetMapping("/subject-stats")
    public Result<SubjectStatsVO> subjectStats() {
        return Result.success(dashboardService.subjectStats());
    }

    /**
     * 本站收藏最多 Top N 热门榜，看板热门排行加载时触发
     */
    @GetMapping("/hot")
    public Result<List<HotSubjectVO>> hot(
            @RequestParam(defaultValue = "10") @Min(1) @Max(50) int limit) {
        return Result.success(dashboardService.hot(limit));
    }
}
