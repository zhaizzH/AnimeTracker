package top.zhaizz.admin.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.admin.mapper.DashboardMapper;
import top.zhaizz.admin.service.DashboardService;
import top.zhaizz.pojo.vo.collection.CollectionStatsVO;
import top.zhaizz.pojo.vo.DailyCount;
import top.zhaizz.pojo.vo.DashboardOverviewVO;
import top.zhaizz.pojo.vo.subject.HotSubjectVO;
import top.zhaizz.pojo.vo.subject.SubjectStatsVO;
import top.zhaizz.pojo.vo.TrendPointVO;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 运营看板服务实现
 */
@Service
@RequiredArgsConstructor
public class DashboardServiceImpl implements DashboardService {

    private final DashboardMapper dashboardMapper;

    @Override
    public DashboardOverviewVO overview() {
        return dashboardMapper.overview();
    }

    @Override
    public List<TrendPointVO> trends(int days) {
        int d = Math.min(Math.max(days, 1), 90);
        LocalDate since = LocalDate.now().minusDays(d - 1L);
        Map<LocalDate, Long> users = dailyMap(dashboardMapper.countUsersByDay(since));
        Map<LocalDate, Long> collections = dailyMap(dashboardMapper.countCollectionsByDay(since));
        Map<LocalDate, Long> logins = dailyMap(dashboardMapper.countLoginsByDay(since));
        List<TrendPointVO> list = new ArrayList<>();
        for (int i = 0; i < d; i++) {
            LocalDate date = since.plusDays(i);
            TrendPointVO vo = new TrendPointVO();
            vo.setDate(date);
            vo.setNewUsers(users.getOrDefault(date, 0L));
            vo.setNewCollections(collections.getOrDefault(date, 0L));
            vo.setLogins(logins.getOrDefault(date, 0L));
            list.add(vo);
        }
        return list;
    }

    private Map<LocalDate, Long> dailyMap(List<DailyCount> rows) {
        return rows.stream().collect(Collectors.toMap(DailyCount::getStatDate, DailyCount::getCnt, (a, b) -> a));
    }

    @Override
    public CollectionStatsVO collectionStats() {
        CollectionStatsVO vo = new CollectionStatsVO();
        vo.setTypes(dashboardMapper.collectionTypeCounts());
        vo.setRatings(dashboardMapper.ratingCounts());
        return vo;
    }

    @Override
    public SubjectStatsVO subjectStats() {
        SubjectStatsVO vo = new SubjectStatsVO();
        vo.setSeasons(dashboardMapper.seasonCounts());
        vo.setImportStatuses(dashboardMapper.subjectStatusCounts());
        vo.setImportStat(dashboardMapper.importStats());
        vo.setScoreCounts(dashboardMapper.subjectScoreCounts());
        return vo;
    }

    @Override
    public List<HotSubjectVO> hot(int limit) {
        return dashboardMapper.hotSubjects(Math.min(Math.max(limit, 1), 50));
    }
}
