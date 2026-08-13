package top.zhaizz.pojo.vo.subject;

import lombok.Data;
import top.zhaizz.pojo.vo.ImportStatVO;
import top.zhaizz.pojo.vo.dashboard.RatingCountVO;

import java.util.List;

/**
 * 番剧/导入统计 VO
 */
@Data
public class SubjectStatsVO {
    private List<SeasonCountVO> seasons;            // 各季度条目数
    private List<SubjectStatusCountVO> importStatuses;   // 导入状态分布
    private ImportStatVO importStat;                // 导入记录统计
    private List<RatingCountVO> scoreCounts;        // 评分分布
}
