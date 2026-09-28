package top.zhaizz.pojo.vo.subject;

import java.util.ArrayList;
import java.util.List;

/** 批量权威回查分类结果 */
public class SubjectBatchResultVO {
    /** 批处理或预览包含的条目集合 */
    private List<SubjectBatchItemVO> items = new ArrayList<>();
    /** 未找到对应记录的标识列表 */
    private List<Long> missingIds = new ArrayList<>();
    /** 被筛选排除的标识列表 */
    private List<Long> filteredIds = new ArrayList<>();
    /** 已收藏条目标识列表 */
    private List<Long> collectedIds = new ArrayList<>();

    /** 创建四个标识集合均为独立空列表的空分类结果 */
    public SubjectBatchResultVO() {
    }

    /**
     * 获取批处理或预览包含的条目集合
     * @return 条目集合；未显式替换时默认为独立空列表
     */
    public List<SubjectBatchItemVO> getItems() {
        return this.items;
    }

    /**
     * 获取未找到对应记录的标识列表
     * @return 缺失标识列表；未显式替换时默认为独立空列表
     */
    public List<Long> getMissingIds() {
        return this.missingIds;
    }

    /**
     * 获取被筛选排除的标识列表
     * @return 被过滤标识列表；未显式替换时默认为独立空列表
     */
    public List<Long> getFilteredIds() {
        return this.filteredIds;
    }

    /**
     * 获取已收藏条目标识列表
     * @return 已收藏标识列表；未显式替换时默认为独立空列表
     */
    public List<Long> getCollectedIds() {
        return this.collectedIds;
    }

    /**
     * 替换批处理或预览包含的条目集合
     * @param items 条目集合，可为 {@code null}；不进行复制
     */
    public void setItems(final List<SubjectBatchItemVO> items) {
        this.items = items;
    }

    /**
     * 替换未找到对应记录的标识列表
     * @param missingIds 缺失标识列表，可为 {@code null}；不进行复制
     */
    public void setMissingIds(final List<Long> missingIds) {
        this.missingIds = missingIds;
    }

    /**
     * 替换被筛选排除的标识列表
     * @param filteredIds 被过滤标识列表，可为 {@code null}；不进行复制
     */
    public void setFilteredIds(final List<Long> filteredIds) {
        this.filteredIds = filteredIds;
    }

    /**
     * 替换已收藏条目标识列表
     * @param collectedIds 已收藏标识列表，可为 {@code null}；不进行复制
     */
    public void setCollectedIds(final List<Long> collectedIds) {
        this.collectedIds = collectedIds;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SubjectBatchResultVO)) return false;
        final SubjectBatchResultVO other = (SubjectBatchResultVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisItems = this.getItems();
        final Object otherItems = other.getItems();
        if (thisItems == null ? otherItems != null : !thisItems.equals(otherItems)) return false;
        final Object thisMissingIds = this.getMissingIds();
        final Object otherMissingIds = other.getMissingIds();
        if (thisMissingIds == null ? otherMissingIds != null : !thisMissingIds.equals(otherMissingIds)) return false;
        final Object thisFilteredIds = this.getFilteredIds();
        final Object otherFilteredIds = other.getFilteredIds();
        if (thisFilteredIds == null ? otherFilteredIds != null : !thisFilteredIds.equals(otherFilteredIds)) return false;
        final Object thisCollectedIds = this.getCollectedIds();
        final Object otherCollectedIds = other.getCollectedIds();
        if (thisCollectedIds == null ? otherCollectedIds != null : !thisCollectedIds.equals(otherCollectedIds)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SubjectBatchResultVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashItems = this.getItems();
        result = result * PRIME + (hashItems == null ? 43 : hashItems.hashCode());
        final Object hashMissingIds = this.getMissingIds();
        result = result * PRIME + (hashMissingIds == null ? 43 : hashMissingIds.hashCode());
        final Object hashFilteredIds = this.getFilteredIds();
        result = result * PRIME + (hashFilteredIds == null ? 43 : hashFilteredIds.hashCode());
        final Object hashCollectedIds = this.getCollectedIds();
        result = result * PRIME + (hashCollectedIds == null ? 43 : hashCollectedIds.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SubjectBatchResultVO(items=" + this.getItems() + ", missingIds=" + this.getMissingIds() + ", filteredIds=" + this.getFilteredIds() + ", collectedIds=" + this.getCollectedIds() + ")";
    }
}
