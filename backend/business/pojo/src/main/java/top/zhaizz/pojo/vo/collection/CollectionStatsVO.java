package top.zhaizz.pojo.vo.collection;

import top.zhaizz.pojo.vo.dashboard.RatingCountVO;
import top.zhaizz.pojo.vo.dashboard.TypeCountVO;

import java.util.List;

/**
 * 收藏统计 VO
 */
public class CollectionStatsVO {

    /** 各收藏类型数量分布 */
    private List<TypeCountVO> types; // 各收藏类型数量分布
    /** 各评分数量分布 */
    private List<RatingCountVO> ratings; // 各评分数量分布

    /** 创建字段均为默认值的空统计对象 */
    public CollectionStatsVO() {
    }

    /**
     * 获取各收藏类型数量分布
     * @return 按收藏类型聚合的数量列表；未提供时为 {@code null}
     */
    public List<TypeCountVO> getTypes() {
        return this.types;
    }

    /**
     * 获取各评分数量分布
     * @return 按评分值聚合的数量列表；未提供时为 {@code null}
     */
    public List<RatingCountVO> getRatings() {
        return this.ratings;
    }

    /**
     * 替换各收藏类型数量分布
     * @param types 按收藏类型聚合的数量列表，可为 {@code null}
     */
    public void setTypes(final List<TypeCountVO> types) {
        this.types = types;
    }

    /**
     * 替换各评分数量分布
     * @param ratings 按评分值聚合的数量列表，可为 {@code null}
     */
    public void setRatings(final List<RatingCountVO> ratings) {
        this.ratings = ratings;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionStatsVO)) return false;
        final CollectionStatsVO other = (CollectionStatsVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisTypes = this.getTypes();
        final Object otherTypes = other.getTypes();
        if (thisTypes == null ? otherTypes != null : !thisTypes.equals(otherTypes)) return false;
        final Object thisRatings = this.getRatings();
        final Object otherRatings = other.getRatings();
        if (thisRatings == null ? otherRatings != null : !thisRatings.equals(otherRatings)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CollectionStatsVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashTypes = this.getTypes();
        result = result * PRIME + (hashTypes == null ? 43 : hashTypes.hashCode());
        final Object hashRatings = this.getRatings();
        result = result * PRIME + (hashRatings == null ? 43 : hashRatings.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CollectionStatsVO(types=" + this.getTypes() + ", ratings=" + this.getRatings() + ")";
    }
}
