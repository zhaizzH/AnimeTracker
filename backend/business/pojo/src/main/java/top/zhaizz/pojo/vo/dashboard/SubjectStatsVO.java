package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.util.List;

/**
 * 番剧/导入统计 VO
 */
@Data
public class SubjectStatsVO {
    private List<SeasonCountVO> seasons;
    private List<SubjectStatusCountVO> importStatuses;
    private ImportStatVO importStat;
    private List<RatingCountVO> scoreCounts;
}
