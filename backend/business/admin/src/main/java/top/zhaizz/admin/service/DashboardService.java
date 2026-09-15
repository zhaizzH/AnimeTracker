package top.zhaizz.admin.service;

import top.zhaizz.pojo.vo.collection.CollectionStatsVO;
import top.zhaizz.pojo.vo.dashboard.DashboardOverviewVO;
import top.zhaizz.pojo.vo.subject.HotSubjectVO;
import top.zhaizz.pojo.vo.subject.SubjectStatsVO;
import top.zhaizz.pojo.vo.dashboard.TrendPointVO;

import java.util.List;

/**
 * 运营看板服务
 */
public interface DashboardService {

    /**
     * 获取看板总览（用户/番剧/收藏等核心运营指标）
     * @return 用户、条目与收藏总览指标
     */
    DashboardOverviewVO overview();

    /**
     * 获取最近 days 天每日新增用户/收藏与登录次数趋势
     * @param days 查询天数，服务层限制为 1–90 天
     * @return 按日期升序排列的趋势点，缺失日期补零
     */
    List<TrendPointVO> trends(int days);

    /**
     * 获取收藏类型与评分分布
     * @return 收藏状态与评分分布
     */
    CollectionStatsVO collectionStats();

    /**
     * 获取番剧季度数量、导入状态与导入记录统计
     * @return 条目季度、导入状态与评分统计
     */
    SubjectStatsVO subjectStats();

    /**
     * 获取本站收藏最多 Top limit 热门番剧
     * @param limit 最多返回的记录数
     * @return 按本站收藏热度排列的条目，最多 50 条
     */
    List<HotSubjectVO> hot(int limit);
}
