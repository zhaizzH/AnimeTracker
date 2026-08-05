package top.zhaizz.admin.service;

import top.zhaizz.pojo.vo.dashboard.CollectionStatsVO;
import top.zhaizz.pojo.vo.dashboard.DashboardOverviewVO;
import top.zhaizz.pojo.vo.dashboard.TrendPointVO;

import java.util.List;

/**
 * 运营看板服务
 */
public interface DashboardService {

    DashboardOverviewVO overview();

    List<TrendPointVO> trends(int days);

    CollectionStatsVO collectionStats();
}
