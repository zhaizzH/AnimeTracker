package top.zhaizz.pojo.vo.collection;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 本周追番进度预览返回体
 */
public class CollectionProgressPreviewVO {

    /** 预览ID */
    private String previewId; // 预览ID
    /** 预览状态 */
    private CollectionProgressState state; // 预览状态
    /** 过期时间 */
    private OffsetDateTime expiresAt; // 过期时间
    /** 本周周一 */
    private LocalDate weekStart; // 本周周一
    /** 截止日期（昨日） */
    private LocalDate cutoffDate; // 截止日期（昨日）
    /** 批处理或预览包含的条目集合 */
    private List<CollectionProgressItemVO> items; // 批处理或预览包含的条目集合

    /**
     * 创建空预览，条目集合初始化为独立空列表
     */
    public CollectionProgressPreviewVO() {
        this.items = defaultItems();
    }

    /**
     * 创建携带全部字段的预览，条目集合原样引用不复制
     * @param previewId 预览ID，可为 {@code null}
     * @param state 预览状态，可为 {@code null}
     * @param expiresAt 过期时间，可为 {@code null}
     * @param weekStart 本周周一，可为 {@code null}
     * @param cutoffDate 截止日期，可为 {@code null}
     * @param items 预览包含的条目集合，可为 {@code null}；不进行复制
     */
    public CollectionProgressPreviewVO(final String previewId, final CollectionProgressState state, final OffsetDateTime expiresAt, final LocalDate weekStart, final LocalDate cutoffDate, final List<CollectionProgressItemVO> items) {
        this.previewId = previewId;
        this.state = state;
        this.expiresAt = expiresAt;
        this.weekStart = weekStart;
        this.cutoffDate = cutoffDate;
        this.items = items;
    }

    /**
     * 创建构建器，用于链式组装预览
     * @return 空的预览构建器
     */
    public static CollectionProgressPreviewVOBuilder builder() {
        return new CollectionProgressPreviewVOBuilder();
    }

    /**
     * 获取预览ID
     * @return 预览ID；未提供时为 {@code null}
     */
    public String getPreviewId() {
        return this.previewId;
    }

    /**
     * 获取预览状态
     * @return 预览状态；未提供时为 {@code null}
     */
    public CollectionProgressState getState() {
        return this.state;
    }

    /**
     * 获取过期时间
     * @return 预览过期时间；未提供时为 {@code null}
     */
    public OffsetDateTime getExpiresAt() {
        return this.expiresAt;
    }

    /**
     * 获取本周周一
     * @return 本周周一日期；未提供时为 {@code null}
     */
    public LocalDate getWeekStart() {
        return this.weekStart;
    }

    /**
     * 获取截止日期
     * @return 纳入统计的截止日期（昨日）；未提供时为 {@code null}
     */
    public LocalDate getCutoffDate() {
        return this.cutoffDate;
    }

    /**
     * 获取预览包含的条目集合
     * @return 条目集合；未通过构建器或构造器提供时为独立空列表，显式传入 {@code null} 时保持 {@code null}
     */
    public List<CollectionProgressItemVO> getItems() {
        return this.items;
    }

    /**
     * 替换预览ID
     * @param previewId 预览ID，可为 {@code null}
     */
    public void setPreviewId(final String previewId) {
        this.previewId = previewId;
    }

    /**
     * 替换预览状态
     * @param state 预览状态，可为 {@code null}
     */
    public void setState(final CollectionProgressState state) {
        this.state = state;
    }

    /**
     * 替换过期时间
     * @param expiresAt 预览过期时间，可为 {@code null}
     */
    public void setExpiresAt(final OffsetDateTime expiresAt) {
        this.expiresAt = expiresAt;
    }

    /**
     * 替换本周周一
     * @param weekStart 本周周一日期，可为 {@code null}
     */
    public void setWeekStart(final LocalDate weekStart) {
        this.weekStart = weekStart;
    }

    /**
     * 替换截止日期
     * @param cutoffDate 纳入统计的截止日期（昨日），可为 {@code null}
     */
    public void setCutoffDate(final LocalDate cutoffDate) {
        this.cutoffDate = cutoffDate;
    }

    /**
     * 替换预览包含的条目集合
     * @param items 条目集合，可为 {@code null}；不进行复制
     */
    public void setItems(final List<CollectionProgressItemVO> items) {
        this.items = items;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionProgressPreviewVO)) return false;
        final CollectionProgressPreviewVO other = (CollectionProgressPreviewVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisPreviewId = this.getPreviewId();
        final Object otherPreviewId = other.getPreviewId();
        if (thisPreviewId == null ? otherPreviewId != null : !thisPreviewId.equals(otherPreviewId)) return false;
        final Object thisState = this.getState();
        final Object otherState = other.getState();
        if (thisState == null ? otherState != null : !thisState.equals(otherState)) return false;
        final Object thisExpiresAt = this.getExpiresAt();
        final Object otherExpiresAt = other.getExpiresAt();
        if (thisExpiresAt == null ? otherExpiresAt != null : !thisExpiresAt.equals(otherExpiresAt)) return false;
        final Object thisWeekStart = this.getWeekStart();
        final Object otherWeekStart = other.getWeekStart();
        if (thisWeekStart == null ? otherWeekStart != null : !thisWeekStart.equals(otherWeekStart)) return false;
        final Object thisCutoffDate = this.getCutoffDate();
        final Object otherCutoffDate = other.getCutoffDate();
        if (thisCutoffDate == null ? otherCutoffDate != null : !thisCutoffDate.equals(otherCutoffDate)) return false;
        final Object thisItems = this.getItems();
        final Object otherItems = other.getItems();
        if (thisItems == null ? otherItems != null : !thisItems.equals(otherItems)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CollectionProgressPreviewVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashPreviewId = this.getPreviewId();
        result = result * PRIME + (hashPreviewId == null ? 43 : hashPreviewId.hashCode());
        final Object hashState = this.getState();
        result = result * PRIME + (hashState == null ? 43 : hashState.hashCode());
        final Object hashExpiresAt = this.getExpiresAt();
        result = result * PRIME + (hashExpiresAt == null ? 43 : hashExpiresAt.hashCode());
        final Object hashWeekStart = this.getWeekStart();
        result = result * PRIME + (hashWeekStart == null ? 43 : hashWeekStart.hashCode());
        final Object hashCutoffDate = this.getCutoffDate();
        result = result * PRIME + (hashCutoffDate == null ? 43 : hashCutoffDate.hashCode());
        final Object hashItems = this.getItems();
        result = result * PRIME + (hashItems == null ? 43 : hashItems.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CollectionProgressPreviewVO(previewId=" + this.getPreviewId() + ", state=" + this.getState() + ", expiresAt=" + this.getExpiresAt() + ", weekStart=" + this.getWeekStart() + ", cutoffDate=" + this.getCutoffDate() + ", items=" + this.getItems() + ")";
    }

    /**
     * 构造条目集合的独立空列表默认值
     * @return 新的空列表
     */
    private static List<CollectionProgressItemVO> defaultItems() {
        return new ArrayList<>();
    }

    /**
     * {@code CollectionProgressPreviewVO} 的链式构建器
     *
     * <p>未显式设置 {@code items} 时在 {@link #build()} 中获得新的空列表，
     * 显式传入 {@code null} 则保持 {@code null}
     */
    public static class CollectionProgressPreviewVOBuilder {
        /** 预览ID */
        private String previewId;
        /** 预览状态 */
        private CollectionProgressState state;
        /** 过期时间 */
        private OffsetDateTime expiresAt;
        /** 本周周一 */
        private LocalDate weekStart;
        /** 截止日期（昨日） */
        private LocalDate cutoffDate;
        /** 是否已显式设置条目集合 */
        private boolean itemsSet;
        /** 显式设置的条目集合 */
        private List<CollectionProgressItemVO> itemsValue;

        /**
         * 创建空构建器，条目集合保持未设置状态
         */
        CollectionProgressPreviewVOBuilder() {
        }

        /**
         * 设置预览ID，覆盖此前取值
         * @param previewId 预览ID，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressPreviewVO.CollectionProgressPreviewVOBuilder previewId(final String previewId) {
            this.previewId = previewId;
            return this;
        }

        /**
         * 设置预览状态，覆盖此前取值
         * @param state 预览状态，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressPreviewVO.CollectionProgressPreviewVOBuilder state(final CollectionProgressState state) {
            this.state = state;
            return this;
        }

        /**
         * 设置过期时间，覆盖此前取值
         * @param expiresAt 预览过期时间，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressPreviewVO.CollectionProgressPreviewVOBuilder expiresAt(final OffsetDateTime expiresAt) {
            this.expiresAt = expiresAt;
            return this;
        }

        /**
         * 设置本周周一，覆盖此前取值
         * @param weekStart 本周周一日期，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressPreviewVO.CollectionProgressPreviewVOBuilder weekStart(final LocalDate weekStart) {
            this.weekStart = weekStart;
            return this;
        }

        /**
         * 设置截止日期，覆盖此前取值
         * @param cutoffDate 纳入统计的截止日期（昨日），可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressPreviewVO.CollectionProgressPreviewVOBuilder cutoffDate(final LocalDate cutoffDate) {
            this.cutoffDate = cutoffDate;
            return this;
        }

        /**
         * 设置条目集合，覆盖此前取值
         * @param items 条目集合，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressPreviewVO.CollectionProgressPreviewVOBuilder items(final List<CollectionProgressItemVO> items) {
            this.itemsValue = items;
            itemsSet = true;
            return this;
        }

        /**
         * 构建预览，未设置的条目集合获得新的空列表
         * @return 携带当前构建器取值的预览
         */
        public CollectionProgressPreviewVO build() {
            List<CollectionProgressItemVO> itemsValue = this.itemsValue;
            if (!this.itemsSet) itemsValue = CollectionProgressPreviewVO.defaultItems();
            return new CollectionProgressPreviewVO(this.previewId, this.state, this.expiresAt, this.weekStart, this.cutoffDate, itemsValue);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本，条目集合以 {@code itemsValue} 形式展示
         */
        @Override
        public String toString() {
            return "CollectionProgressPreviewVO.CollectionProgressPreviewVOBuilder(previewId=" + this.previewId + ", state=" + this.state + ", expiresAt=" + this.expiresAt + ", weekStart=" + this.weekStart + ", cutoffDate=" + this.cutoffDate + ", itemsValue=" + this.itemsValue + ")";
        }
    }
}
