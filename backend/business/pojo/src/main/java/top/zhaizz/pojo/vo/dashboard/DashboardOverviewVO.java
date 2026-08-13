package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 看板总览 VO
 */
@Data
public class DashboardOverviewVO {
    private long userCount;             // 用户总数
    private long subjectCount;          // 条目总数
    private long collectionCount;       // 收藏总数
    private long episodeCount;          // 剧集总数
    private long importCount;           // 导入记录总数
    private long todayNewUsers;         // 今日新增用户
    private long todayNewCollections;   // 今日新增收藏
    private long todayLogins;           // 今日登录次数
}
