package top.zhaizz.admin.mapper;

import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.vo.dashboard.DailyCountVO;
import top.zhaizz.pojo.vo.dashboard.DashboardOverviewVO;
import top.zhaizz.pojo.vo.subject.HotSubjectVO;
import top.zhaizz.pojo.vo.imprt.ImportStatVO;
import top.zhaizz.pojo.vo.dashboard.RatingCountVO;
import top.zhaizz.pojo.vo.subject.SeasonCountVO;
import top.zhaizz.pojo.vo.subject.SubjectStatusCountVO;
import top.zhaizz.pojo.vo.dashboard.TypeCountVO;

import java.time.LocalDate;
import java.util.List;

/**
 * 运营看板聚合查询 Mapper
 */
public interface DashboardMapper {

    /**
     * 聚合统计用户/番剧/收藏/集数/导入总量及今日新增，返回看板总览
     */
    DashboardOverviewVO overview();

    /**
     * 按日统计 since 起的每日新增用户数
     */
    List<DailyCountVO> countUsersByDay(@Param("since") LocalDate since);

    /**
     * 按日统计 since 起的每日新增收藏数
     */
    List<DailyCountVO> countCollectionsByDay(@Param("since") LocalDate since);

    /**
     * 按日统计 since 起的每日成功登录次数
     */
    List<DailyCountVO> countLoginsByDay(@Param("since") LocalDate since);

    /**
     * 统计各收藏类型的收藏数
     */
    List<TypeCountVO> collectionTypeCounts();

    /**
     * 统计各评分档（rate>0）的用户收藏数
     */
    List<RatingCountVO> ratingCounts();

    /**
     * 统计各分数档（score>0）的番剧数
     */
    List<RatingCountVO> subjectScoreCounts();

    /**
     * 按播出季度聚合番剧数（由 air_date 推导季度）
     */
    List<SeasonCountVO> seasonCounts();

    /**
     * 统计各导入状态的番剧数
     */
    List<SubjectStatusCountVO> subjectStatusCounts();

    /**
     * 聚合导入任务总数、成功数与失败数
     */
    ImportStatVO importStats();

    /**
     * 按收藏数降序取前 limit 条热门番剧
     */
    List<HotSubjectVO> hotSubjects(@Param("limit") int limit);
}
