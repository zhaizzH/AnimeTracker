package top.zhaizz.client.model;

import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressItemVO;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 收藏进度预览 Redis 快照（内部存储，永不直接作为 HTTP 返回）
 */
public class ProgressPreviewSnapshot {
    /**
     * 预览ID
     */
    private String previewId; // 预览ID
    /**
     * 用户ID
     */
    private Long userId; // 用户ID
    /**
     * 快照状态
     */
    private ProgressPreviewStatus status; // 快照状态
    /**
     * 本周周一
     */
    private LocalDate weekStart; // 本周周一
    /**
     * 截止日期（昨日）
     */
    private LocalDate cutoffDate; // 截止日期（昨日）
    /**
     * 待处理条目集合
     */
    private List<CollectionProgressItemVO> items;
    /**
     * 创建时间
     */
    private OffsetDateTime createdAt; // 创建时间
    /**
     * 过期时间
     */
    private OffsetDateTime expiresAt; // 过期时间
    /**
     * 执行结果（COMPLETED 后用于幂等重放）
     */
    private CollectionProgressExecutionVO executionResult; // 执行结果（COMPLETED 后用于幂等重放）

    /** 创建字段均为默认值的空快照，待处理条目集合为可变空列表以兼容 Jackson 反序列化 */
    public ProgressPreviewSnapshot() {
        this.items = ProgressPreviewSnapshot.defaultItems();
    }

    /**
     * 创建携带全部字段的快照
     * @param previewId 预览ID，可为 {@code null}
     * @param userId 用户ID，可为 {@code null}
     * @param status 快照状态，可为 {@code null}
     * @param weekStart 本周周一，可为 {@code null}
     * @param cutoffDate 截止日期，可为 {@code null}
     * @param items 待处理条目集合，可为 {@code null}
     * @param createdAt 创建时间，可为 {@code null}
     * @param expiresAt 过期时间，可为 {@code null}
     * @param executionResult 执行结果，可为 {@code null}
     */
    public ProgressPreviewSnapshot(final String previewId, final Long userId, final ProgressPreviewStatus status, final LocalDate weekStart, final LocalDate cutoffDate, final List<CollectionProgressItemVO> items, final OffsetDateTime createdAt, final OffsetDateTime expiresAt, final CollectionProgressExecutionVO executionResult) {
        this.previewId = previewId;
        this.userId = userId;
        this.status = status;
        this.weekStart = weekStart;
        this.cutoffDate = cutoffDate;
        this.items = items;
        this.createdAt = createdAt;
        this.expiresAt = expiresAt;
        this.executionResult = executionResult;
    }

    /**
     * 创建快照的链式构建器
     * @return 空的快照构建器
     */
    public static ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder builder() {
        return new ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder();
    }

    /**
     * 提供待处理条目集合默认值的辅助方法
     * @return 新创建的可变空列表
     */
    private static List<CollectionProgressItemVO> defaultItems() {
        return new ArrayList<>();
    }

    /**
     * 收藏进度预览快照的链式构建器
     */
    public static class ProgressPreviewSnapshotBuilder {
        /**
         * 预览ID
         */
        private String previewId;
        /**
         * 用户ID
         */
        private Long userId;
        /**
         * 快照状态
         */
        private ProgressPreviewStatus status;
        /**
         * 本周周一
         */
        private LocalDate weekStart;
        /**
         * 截止日期（昨日）
         */
        private LocalDate cutoffDate;
        /**
         * 是否已显式设置待处理条目集合
         */
        private boolean itemsSet;
        /**
         * 待处理条目集合的待构建值
         */
        private List<CollectionProgressItemVO> itemsValue;
        /**
         * 创建时间
         */
        private OffsetDateTime createdAt;
        /**
         * 过期时间
         */
        private OffsetDateTime expiresAt;
        /**
         * 执行结果（COMPLETED 后用于幂等重放）
         */
        private CollectionProgressExecutionVO executionResult;

        /** 创建字段均为默认值的空构建器 */
        ProgressPreviewSnapshotBuilder() {
        }

        /**
         * 设置预览ID
         * @param previewId 预览ID，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder previewId(final String previewId) {
            this.previewId = previewId;
            return this;
        }

        /**
         * 设置用户ID
         * @param userId 用户ID，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder userId(final Long userId) {
            this.userId = userId;
            return this;
        }

        /**
         * 设置快照状态
         * @param status 快照状态，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder status(final ProgressPreviewStatus status) {
            this.status = status;
            return this;
        }

        /**
         * 设置本周周一
         * @param weekStart 本周周一，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder weekStart(final LocalDate weekStart) {
            this.weekStart = weekStart;
            return this;
        }

        /**
         * 设置截止日期
         * @param cutoffDate 截止日期（昨日），可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder cutoffDate(final LocalDate cutoffDate) {
            this.cutoffDate = cutoffDate;
            return this;
        }

        /**
         * 设置待处理条目集合，传入 {@code null} 将保留为 null
         * @param items 待处理条目集合，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder items(final List<CollectionProgressItemVO> items) {
            this.itemsValue = items;
            itemsSet = true;
            return this;
        }

        /**
         * 设置创建时间
         * @param createdAt 创建时间，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder createdAt(final OffsetDateTime createdAt) {
            this.createdAt = createdAt;
            return this;
        }

        /**
         * 设置过期时间
         * @param expiresAt 过期时间，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder expiresAt(final OffsetDateTime expiresAt) {
            this.expiresAt = expiresAt;
            return this;
        }

        /**
         * 设置执行结果
         * @param executionResult 执行结果，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder executionResult(final CollectionProgressExecutionVO executionResult) {
            this.executionResult = executionResult;
            return this;
        }

        /**
         * 依据已设置的字段构建快照实例，未显式设置待处理条目集合时使用空列表
         * @return 使用构建器当前字段值的快照
         */
        public ProgressPreviewSnapshot build() {
            List<CollectionProgressItemVO> itemsValue = this.itemsValue;
            if (!this.itemsSet) itemsValue = ProgressPreviewSnapshot.defaultItems();
            return new ProgressPreviewSnapshot(this.previewId, this.userId, this.status, this.weekStart, this.cutoffDate, itemsValue, this.createdAt, this.expiresAt, this.executionResult);
        }

        /**
         * 返回包含构建器全部字段的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "ProgressPreviewSnapshot.ProgressPreviewSnapshotBuilder(previewId=" + this.previewId + ", userId=" + this.userId + ", status=" + this.status + ", weekStart=" + this.weekStart + ", cutoffDate=" + this.cutoffDate + ", itemsValue=" + this.itemsValue + ", createdAt=" + this.createdAt + ", expiresAt=" + this.expiresAt + ", executionResult=" + this.executionResult + ")";
        }
    }

    /**
     * 获取预览ID
     * @return 快照的唯一标识，未设置时为 {@code null}
     */
    public String getPreviewId() {
        return this.previewId;
    }

    /**
     * 获取用户ID
     * @return 快照所属用户主键，未设置时为 {@code null}
     */
    public Long getUserId() {
        return this.userId;
    }

    /**
     * 获取快照状态
     * @return 预览执行状态，未设置时为 {@code null}
     */
    public ProgressPreviewStatus getStatus() {
        return this.status;
    }

    /**
     * 获取本周周一
     * @return 本次预览所在周的周一日期，未设置时为 {@code null}
     */
    public LocalDate getWeekStart() {
        return this.weekStart;
    }

    /**
     * 获取截止日期
     * @return 进度统计的截止日期（昨日），未设置时为 {@code null}
     */
    public LocalDate getCutoffDate() {
        return this.cutoffDate;
    }

    /**
     * 获取待处理条目集合
     * @return 预览涉及的收藏条目列表；空快照默认为空列表，显式置空时为 {@code null}
     */
    public List<CollectionProgressItemVO> getItems() {
        return this.items;
    }

    /**
     * 获取创建时间
     * @return 快照生成时刻，未设置时为 {@code null}
     */
    public OffsetDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 获取过期时间
     * @return 快照在 Redis 中的失效时刻，未设置时为 {@code null}
     */
    public OffsetDateTime getExpiresAt() {
        return this.expiresAt;
    }

    /**
     * 获取执行结果
     * @return COMPLETED 后用于幂等重放的执行结果，未完成时为 {@code null}
     */
    public CollectionProgressExecutionVO getExecutionResult() {
        return this.executionResult;
    }

    /**
     * 替换预览ID
     * @param previewId 新的快照唯一标识，可为 {@code null}
     */
    public void setPreviewId(final String previewId) {
        this.previewId = previewId;
    }

    /**
     * 替换用户ID
     * @param userId 新的快照所属用户主键，可为 {@code null}
     */
    public void setUserId(final Long userId) {
        this.userId = userId;
    }

    /**
     * 替换快照状态
     * @param status 新的预览执行状态，可为 {@code null}
     */
    public void setStatus(final ProgressPreviewStatus status) {
        this.status = status;
    }

    /**
     * 替换本周周一
     * @param weekStart 新的本周周一日期，可为 {@code null}
     */
    public void setWeekStart(final LocalDate weekStart) {
        this.weekStart = weekStart;
    }

    /**
     * 替换截止日期
     * @param cutoffDate 新的进度统计截止日期，可为 {@code null}
     */
    public void setCutoffDate(final LocalDate cutoffDate) {
        this.cutoffDate = cutoffDate;
    }

    /**
     * 替换待处理条目集合
     * @param items 新的收藏条目列表，可为 {@code null}
     */
    public void setItems(final List<CollectionProgressItemVO> items) {
        this.items = items;
    }

    /**
     * 替换创建时间
     * @param createdAt 新的快照生成时刻，可为 {@code null}
     */
    public void setCreatedAt(final OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 替换过期时间
     * @param expiresAt 新的快照失效时刻，可为 {@code null}
     */
    public void setExpiresAt(final OffsetDateTime expiresAt) {
        this.expiresAt = expiresAt;
    }

    /**
     * 替换执行结果
     * @param executionResult 新的用于幂等重放的执行结果，可为 {@code null}
     */
    public void setExecutionResult(final CollectionProgressExecutionVO executionResult) {
        this.executionResult = executionResult;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ProgressPreviewSnapshot)) return false;
        final ProgressPreviewSnapshot other = (ProgressPreviewSnapshot) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisUserId = this.getUserId();
        final Object otherUserId = other.getUserId();
        if (thisUserId == null ? otherUserId != null : !thisUserId.equals(otherUserId)) return false;
        final Object thisPreviewId = this.getPreviewId();
        final Object otherPreviewId = other.getPreviewId();
        if (thisPreviewId == null ? otherPreviewId != null : !thisPreviewId.equals(otherPreviewId)) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        final Object thisWeekStart = this.getWeekStart();
        final Object otherWeekStart = other.getWeekStart();
        if (thisWeekStart == null ? otherWeekStart != null : !thisWeekStart.equals(otherWeekStart)) return false;
        final Object thisCutoffDate = this.getCutoffDate();
        final Object otherCutoffDate = other.getCutoffDate();
        if (thisCutoffDate == null ? otherCutoffDate != null : !thisCutoffDate.equals(otherCutoffDate)) return false;
        final Object thisItems = this.getItems();
        final Object otherItems = other.getItems();
        if (thisItems == null ? otherItems != null : !thisItems.equals(otherItems)) return false;
        final Object thisCreatedAt = this.getCreatedAt();
        final Object otherCreatedAt = other.getCreatedAt();
        if (thisCreatedAt == null ? otherCreatedAt != null : !thisCreatedAt.equals(otherCreatedAt)) return false;
        final Object thisExpiresAt = this.getExpiresAt();
        final Object otherExpiresAt = other.getExpiresAt();
        if (thisExpiresAt == null ? otherExpiresAt != null : !thisExpiresAt.equals(otherExpiresAt)) return false;
        final Object thisExecutionResult = this.getExecutionResult();
        final Object otherExecutionResult = other.getExecutionResult();
        if (thisExecutionResult == null ? otherExecutionResult != null : !thisExecutionResult.equals(otherExecutionResult)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ProgressPreviewSnapshot;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashUserId = this.getUserId();
        result = result * PRIME + (hashUserId == null ? 43 : hashUserId.hashCode());
        final Object hashPreviewId = this.getPreviewId();
        result = result * PRIME + (hashPreviewId == null ? 43 : hashPreviewId.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        final Object hashWeekStart = this.getWeekStart();
        result = result * PRIME + (hashWeekStart == null ? 43 : hashWeekStart.hashCode());
        final Object hashCutoffDate = this.getCutoffDate();
        result = result * PRIME + (hashCutoffDate == null ? 43 : hashCutoffDate.hashCode());
        final Object hashItems = this.getItems();
        result = result * PRIME + (hashItems == null ? 43 : hashItems.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        final Object hashExpiresAt = this.getExpiresAt();
        result = result * PRIME + (hashExpiresAt == null ? 43 : hashExpiresAt.hashCode());
        final Object hashExecutionResult = this.getExecutionResult();
        result = result * PRIME + (hashExecutionResult == null ? 43 : hashExecutionResult.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ProgressPreviewSnapshot(previewId=" + this.getPreviewId() + ", userId=" + this.getUserId() + ", status=" + this.getStatus() + ", weekStart=" + this.getWeekStart() + ", cutoffDate=" + this.getCutoffDate() + ", items=" + this.getItems() + ", createdAt=" + this.getCreatedAt() + ", expiresAt=" + this.getExpiresAt() + ", executionResult=" + this.getExecutionResult() + ")";
    }
}
