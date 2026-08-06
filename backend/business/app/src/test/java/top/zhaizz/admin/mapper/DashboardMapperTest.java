package top.zhaizz.admin.mapper;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import top.zhaizz.app.AppApplication;
import top.zhaizz.pojo.vo.dashboard.DashboardOverviewVO;

import java.time.LocalDate;

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
}
