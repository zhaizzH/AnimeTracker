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
import top.zhaizz.pojo.vo.dashboard.DashboardOverviewVO;
import top.zhaizz.pojo.vo.subject.HotSubjectVO;
import top.zhaizz.pojo.vo.subject.SubjectStatsVO;
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

    /** 管理员仪表盘统计服务 */
    private final DashboardService dashboardService;

    /**
     * 看板总览，管理后台进入看板页时加载核心运营指标
     * @return 统一成功响应，其数据为：用户、条目与收藏总览指标
     */
    @GetMapping("/overview")
    public Result<DashboardOverviewVO> overview() {
        return Result.success(dashboardService.overview());
    }

    /**
     * 每日趋势（新增用户/收藏/登录），看板趋势图展示时触发
     * @param days 查询天数，服务层限制为 1–90 天
     * @return 统一成功响应，其数据为：按日期升序排列的趋势点，缺失日期补零
     */
    @GetMapping("/trends")
    public Result<List<TrendPointVO>> trends(
            @RequestParam(defaultValue = "30") @Min(1) @Max(90) int days) {
        return Result.success(dashboardService.trends(days));
    }

    /**
     * 收藏类型与评分分布，看板分布图加载时触发
     * @return 统一成功响应，其数据为：收藏状态与评分分布
     */
    @GetMapping("/collection-stats")
    public Result<CollectionStatsVO> collectionStats() {
        return Result.success(dashboardService.collectionStats());
    }

    /**
     * 番剧季度数量、导入状态与导入记录统计，看板内容面板加载时触发
     * @return 统一成功响应，其数据为：条目季度、导入状态与评分统计
     */
    @GetMapping("/subject-stats")
    public Result<SubjectStatsVO> subjectStats() {
        return Result.success(dashboardService.subjectStats());
    }

    /**
     * 本站收藏最多 Top N 热门榜，看板热门排行加载时触发
     * @param limit 最多返回的记录数
     * @return 统一成功响应，其数据为：按本站收藏热度排列的条目，最多 50 条
     */
    @GetMapping("/hot")
    public Result<List<HotSubjectVO>> hot(
            @RequestParam(defaultValue = "10") @Min(1) @Max(50) int limit) {
        return Result.success(dashboardService.hot(limit));
    }
}
