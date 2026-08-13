package top.zhaizz.admin.service;

import top.zhaizz.pojo.vo.CollectionStatsVO;
import top.zhaizz.pojo.vo.DashboardOverviewVO;
import top.zhaizz.pojo.vo.subject.HotSubjectVO;
import top.zhaizz.pojo.vo.subject.SubjectStatsVO;
import top.zhaizz.pojo.vo.TrendPointVO;

import java.util.List;

/**
 * 运营看板服务
 */
public interface DashboardService {

    /**
     * 获取看板总览（用户/番剧/收藏等核心运营指标）
     */
    DashboardOverviewVO overview();

    /**
     * 获取最近 days 天每日新增用户/收藏与登录次数趋势
     */
    List<TrendPointVO> trends(int days);

    /**
     * 获取收藏类型与评分分布
     */
    CollectionStatsVO collectionStats();

    /**
     * 获取番剧季度数量、导入状态与导入记录统计
     */
    SubjectStatsVO subjectStats();

    /**
     * 获取本站收藏最多 Top limit 热门番剧
     */
    List<HotSubjectVO> hot(int limit);
}
