package top.zhaizz.pojo.vo.subject;

import top.zhaizz.pojo.vo.imprt.ImportStatVO;
import top.zhaizz.pojo.vo.dashboard.RatingCountVO;

import java.util.List;

/**
 * 番剧/导入统计 VO
 */
public class SubjectStatsVO {
    /** 各季度条目数 */
    private List<SeasonCountVO> seasons;            // 各季度条目数
    /** 导入状态分布 */
    private List<SubjectStatusCountVO> importStatuses;   // 导入状态分布
    /** 导入记录统计 */
    private ImportStatVO importStat;                // 导入记录统计
    /** 评分分布 */
    private List<RatingCountVO> scoreCounts;        // 评分分布

    /** 创建字段均为默认值的空统计结果 */
    public SubjectStatsVO() {
    }

    /**
     * 获取各季度条目数
     * @return 按季度聚合的条目数量列表；未提供时为 {@code null}
     */
    public List<SeasonCountVO> getSeasons() {
        return this.seasons;
    }

    /**
     * 获取导入状态分布
     * @return 各导入状态对应的条目数量列表；未提供时为 {@code null}
     */
    public List<SubjectStatusCountVO> getImportStatuses() {
        return this.importStatuses;
    }

    /**
     * 获取导入记录统计
     * @return 导入记录的汇总统计；未提供时为 {@code null}
     */
    public ImportStatVO getImportStat() {
        return this.importStat;
    }

    /**
     * 获取评分分布
     * @return 按评分档位聚合的数量列表；未提供时为 {@code null}
     */
    public List<RatingCountVO> getScoreCounts() {
        return this.scoreCounts;
    }

    /**
     * 替换各季度条目数
     * @param seasons 按季度聚合的条目数量列表，可为 {@code null}；不进行复制
     */
    public void setSeasons(final List<SeasonCountVO> seasons) {
        this.seasons = seasons;
    }

    /**
     * 替换导入状态分布
     * @param importStatuses 各导入状态对应的条目数量列表，可为 {@code null}；不进行复制
     */
    public void setImportStatuses(final List<SubjectStatusCountVO> importStatuses) {
        this.importStatuses = importStatuses;
    }

    /**
     * 替换导入记录统计
     * @param importStat 导入记录的汇总统计，可为 {@code null}
     */
    public void setImportStat(final ImportStatVO importStat) {
        this.importStat = importStat;
    }

    /**
     * 替换评分分布
     * @param scoreCounts 按评分档位聚合的数量列表，可为 {@code null}；不进行复制
     */
    public void setScoreCounts(final List<RatingCountVO> scoreCounts) {
        this.scoreCounts = scoreCounts;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectStatsVO)) return false;
        final SubjectStatsVO other = (SubjectStatsVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSeasons = this.getSeasons();
        final Object otherSeasons = other.getSeasons();
        if (thisSeasons == null ? otherSeasons != null : !thisSeasons.equals(otherSeasons)) return false;
        final Object thisImportStatuses = this.getImportStatuses();
        final Object otherImportStatuses = other.getImportStatuses();
        if (thisImportStatuses == null ? otherImportStatuses != null : !thisImportStatuses.equals(otherImportStatuses)) return false;
        final Object thisImportStat = this.getImportStat();
        final Object otherImportStat = other.getImportStat();
        if (thisImportStat == null ? otherImportStat != null : !thisImportStat.equals(otherImportStat)) return false;
        final Object thisScoreCounts = this.getScoreCounts();
        final Object otherScoreCounts = other.getScoreCounts();
        if (thisScoreCounts == null ? otherScoreCounts != null : !thisScoreCounts.equals(otherScoreCounts)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectStatsVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashSeasons = this.getSeasons();
        result = result * PRIME + (hashSeasons == null ? 43 : hashSeasons.hashCode());
        final Object hashImportStatuses = this.getImportStatuses();
        result = result * PRIME + (hashImportStatuses == null ? 43 : hashImportStatuses.hashCode());
        final Object hashImportStat = this.getImportStat();
        result = result * PRIME + (hashImportStat == null ? 43 : hashImportStat.hashCode());
        final Object hashScoreCounts = this.getScoreCounts();
        result = result * PRIME + (hashScoreCounts == null ? 43 : hashScoreCounts.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectStatsVO(seasons=" + this.getSeasons() + ", importStatuses=" + this.getImportStatuses() + ", importStat=" + this.getImportStat() + ", scoreCounts=" + this.getScoreCounts() + ")";
    }
}
