package top.zhaizz.admin.mapper;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import top.zhaizz.app.AppApplication;
import top.zhaizz.pojo.vo.DashboardOverviewVO;
import top.zhaizz.pojo.vo.HotSubjectVO;

import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 看板聚合查询集成测试（需本地 MySQL，application-local.yml 数据源）
 */
@SpringBootTest(classes = AppApplication.class)
@ActiveProfiles("local")
class DashboardMapperTest {

    @Autowired
    private DashboardMapper dashboardMapper;

    @Test
    void aggregateQueriesRunAgainstLocalDb() {
        DashboardOverviewVO overview = dashboardMapper.overview();
        assertThat(overview).isNotNull();
        assertThat(overview.getUserCount()).isGreaterThanOrEqualTo(0);

        assertThat(dashboardMapper.collectionTypeCounts()).isNotNull();
        assertThat(dashboardMapper.ratingCounts()).isNotNull();
        assertThat(dashboardMapper.subjectScoreCounts()).isNotNull();
        assertThat(dashboardMapper.countUsersByDay(LocalDate.now().minusDays(30))).isNotNull();
        assertThat(dashboardMapper.countCollectionsByDay(LocalDate.now().minusDays(30))).isNotNull();
        assertThat(dashboardMapper.countLoginsByDay(LocalDate.now().minusDays(30))).isNotNull();
        assertThat(dashboardMapper.seasonCounts()).isNotNull();
        assertThat(dashboardMapper.subjectStatusCounts()).isNotNull();
        assertThat(dashboardMapper.importStats()).isNotNull();
        assertThat(dashboardMapper.hotSubjects(10)).isNotNull();
    }

    /**
     * 热门榜 collectionCount 映射防护：SQL 别名必须为 collection_count 才能映射到 VO.collectionCount。
     * 当前库中已有收藏，至少一条收藏数应大于 0（回归: 2026-08-11 热门榜收藏数恒为 0 的 bug）。
     */
    @Test
    void hotSubjectsMapCollectionCount() {
        List<HotSubjectVO> hotSubjects = dashboardMapper.hotSubjects(10);
        assertThat(hotSubjects).isNotNull();
        assertThat(hotSubjects)
                .allSatisfy(item -> assertThat(item.getCollectionCount()).isGreaterThanOrEqualTo(0));
        assertThat(hotSubjects)
                .anySatisfy(item -> assertThat(item.getCollectionCount()).isGreaterThan(0));
    }
}
