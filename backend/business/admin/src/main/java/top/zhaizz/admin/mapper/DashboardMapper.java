package top.zhaizz.admin.mapper;

import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.vo.dashboard.CollectionStatsVO;
import top.zhaizz.pojo.vo.dashboard.DailyCount;
import top.zhaizz.pojo.vo.dashboard.DashboardOverviewVO;
import top.zhaizz.pojo.vo.dashboard.RatingCountVO;
import top.zhaizz.pojo.vo.dashboard.TypeCountVO;

import java.time.LocalDate;
import java.util.List;

/**
 * 运营看板聚合查询 Mapper
 */
public interface DashboardMapper {

    DashboardOverviewVO overview();

    List<DailyCount> countUsersByDay(@Param("since") LocalDate since);

    List<DailyCount> countCollectionsByDay(@Param("since") LocalDate since);

    List<DailyCount> countLoginsByDay(@Param("since") LocalDate since);

    List<TypeCountVO> collectionTypeCounts();

    List<RatingCountVO> ratingCounts();
}
