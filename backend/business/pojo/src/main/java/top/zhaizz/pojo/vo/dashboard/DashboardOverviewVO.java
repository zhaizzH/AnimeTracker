package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 看板总览 VO
 */
@Data
public class DashboardOverviewVO {
    private long userCount;
    private long subjectCount;
    private long collectionCount;
    private long episodeCount;
    private long importCount;
    private long todayNewUsers;
    private long todayNewCollections;
    private long todayLogins;
}
