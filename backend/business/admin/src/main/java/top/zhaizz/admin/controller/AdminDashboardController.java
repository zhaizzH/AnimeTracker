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
import top.zhaizz.pojo.vo.dashboard.CollectionStatsVO;
import top.zhaizz.pojo.vo.dashboard.DashboardOverviewVO;
import top.zhaizz.pojo.vo.dashboard.TrendPointVO;

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
     * 看板总览
     */
    @GetMapping("/overview")
    public Result<DashboardOverviewVO> overview() {
        return Result.success(dashboardService.overview());
    }

    /**
     * 每日趋势（新增用户/收藏/登录）
     */
    @GetMapping("/trends")
    public Result<List<TrendPointVO>> trends(
            @RequestParam(defaultValue = "30") @Min(1) @Max(90) int days) {
        return Result.success(dashboardService.trends(days));
    }

    /**
     * 收藏类型与评分分布
     */
    @GetMapping("/collection-stats")
    public Result<CollectionStatsVO> collectionStats() {
        return Result.success(dashboardService.collectionStats());
    }
}
