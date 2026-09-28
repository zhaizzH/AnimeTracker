package top.zhaizz.pojo.vo.collection;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.util.ArrayList;
import java.util.List;

/**
 * 本周追番进度确认执行结果
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class CollectionProgressExecutionVO {

    /** 执行状态 */
    private CollectionProgressState state; // 执行状态
    /** 是否为重复确认返回首次结果 */
    private boolean replayed; // 是否为重复确认返回首次结果
    /** 预览变化时的新预览（COMPLETED 时为 null 不输出） */
    private CollectionProgressPreviewVO preview; // 预览变化时的新预览（COMPLETED 时为 null 不输出）
    /** 执行成功的条目数量 */
    private List<CollectionProgressItemVO> succeeded; // 执行成功的条目数量
    /** 执行时跳过的条目数量 */
    private List<CollectionProgressFailureVO> skipped; // 执行时跳过的条目数量
    /** 执行失败的条目数量 */
    private List<CollectionProgressFailureVO> failed; // 执行失败的条目数量

    /**
     * 创建空结果，三个条目列表初始化为独立空列表
     */
    public CollectionProgressExecutionVO() {
        this.succeeded = defaultSucceeded();
        this.skipped = defaultSkipped();
        this.failed = defaultFailed();
    }

    /**
     * 创建携带全部字段的执行结果
     * @param state 执行状态，可为 {@code null}
     * @param replayed 是否为重复确认返回首次结果
     * @param preview 预览变化时的新预览，可为 {@code null}
     * @param succeeded 执行成功的条目列表，可为 {@code null}；不进行复制
     * @param skipped 执行时跳过的条目列表，可为 {@code null}；不进行复制
     * @param failed 执行失败的条目列表，可为 {@code null}；不进行复制
     */
    public CollectionProgressExecutionVO(final CollectionProgressState state, final boolean replayed, final CollectionProgressPreviewVO preview, final List<CollectionProgressItemVO> succeeded, final List<CollectionProgressFailureVO> skipped, final List<CollectionProgressFailureVO> failed) {
        this.state = state;
        this.replayed = replayed;
        this.preview = preview;
        this.succeeded = succeeded;
        this.skipped = skipped;
        this.failed = failed;
    }

    /**
     * 创建构建器，用于链式组装执行结果
     * @return 空的执行结果构建器
     */
    public static CollectionProgressExecutionVOBuilder builder() {
        return new CollectionProgressExecutionVOBuilder();
    }

    /**
     * 获取执行状态
     * @return 执行状态；未设置时为 {@code null}
     */
    public CollectionProgressState getState() {
        return this.state;
    }

    /**
     * 判断是否为重复确认返回首次结果
     * @return 重复确认且复用首次结果时为 {@code true}
     */
    public boolean isReplayed() {
        return this.replayed;
    }

    /**
     * 获取预览变化时的新预览
     * @return 新预览；无变化或已完成时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public CollectionProgressPreviewVO getPreview() {
        return this.preview;
    }

    /**
     * 获取执行成功的条目列表
     * @return 成功条目；构造时未提供则为独立空列表，显式传入 {@code null} 时保持 {@code null}
     */
    public List<CollectionProgressItemVO> getSucceeded() {
        return this.succeeded;
    }

    /**
     * 获取执行时跳过的条目列表
     * @return 跳过条目；构造时未提供则为独立空列表，显式传入 {@code null} 时保持 {@code null}
     */
    public List<CollectionProgressFailureVO> getSkipped() {
        return this.skipped;
    }

    /**
     * 获取执行失败的条目列表
     * @return 失败条目；构造时未提供则为独立空列表，显式传入 {@code null} 时保持 {@code null}
     */
    public List<CollectionProgressFailureVO> getFailed() {
        return this.failed;
    }

    /**
     * 替换执行状态
     * @param state 执行状态，可为 {@code null}
     */
    public void setState(final CollectionProgressState state) {
        this.state = state;
    }

    /**
     * 替换是否为重复确认返回首次结果的标记
     * @param replayed 重复确认且复用首次结果时为 {@code true}
     */
    public void setReplayed(final boolean replayed) {
        this.replayed = replayed;
    }

    /**
     * 替换预览变化时的新预览
     * @param preview 新预览，可为 {@code null}
     */
    public void setPreview(final CollectionProgressPreviewVO preview) {
        this.preview = preview;
    }

    /**
     * 替换执行成功的条目列表
     * @param succeeded 成功条目，可为 {@code null}；不进行复制
     */
    public void setSucceeded(final List<CollectionProgressItemVO> succeeded) {
        this.succeeded = succeeded;
    }

    /**
     * 替换执行时跳过的条目列表
     * @param skipped 跳过条目，可为 {@code null}；不进行复制
     */
    public void setSkipped(final List<CollectionProgressFailureVO> skipped) {
        this.skipped = skipped;
    }

    /**
     * 替换执行失败的条目列表
     * @param failed 失败条目，可为 {@code null}；不进行复制
     */
    public void setFailed(final List<CollectionProgressFailureVO> failed) {
        this.failed = failed;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionProgressExecutionVO)) return false;
        final CollectionProgressExecutionVO other = (CollectionProgressExecutionVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.isReplayed() != other.isReplayed()) return false;
        final Object thisState = this.getState();
        final Object otherState = other.getState();
        if (thisState == null ? otherState != null : !thisState.equals(otherState)) return false;
        final Object thisPreview = this.getPreview();
        final Object otherPreview = other.getPreview();
        if (thisPreview == null ? otherPreview != null : !thisPreview.equals(otherPreview)) return false;
        final Object thisSucceeded = this.getSucceeded();
        final Object otherSucceeded = other.getSucceeded();
        if (thisSucceeded == null ? otherSucceeded != null : !thisSucceeded.equals(otherSucceeded)) return false;
        final Object thisSkipped = this.getSkipped();
        final Object otherSkipped = other.getSkipped();
        if (thisSkipped == null ? otherSkipped != null : !thisSkipped.equals(otherSkipped)) return false;
        final Object thisFailed = this.getFailed();
        final Object otherFailed = other.getFailed();
        if (thisFailed == null ? otherFailed != null : !thisFailed.equals(otherFailed)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CollectionProgressExecutionVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + (this.isReplayed() ? 79 : 97);
        final Object hashState = this.getState();
        result = result * PRIME + (hashState == null ? 43 : hashState.hashCode());
        final Object hashPreview = this.getPreview();
        result = result * PRIME + (hashPreview == null ? 43 : hashPreview.hashCode());
        final Object hashSucceeded = this.getSucceeded();
        result = result * PRIME + (hashSucceeded == null ? 43 : hashSucceeded.hashCode());
        final Object hashSkipped = this.getSkipped();
        result = result * PRIME + (hashSkipped == null ? 43 : hashSkipped.hashCode());
        final Object hashFailed = this.getFailed();
        result = result * PRIME + (hashFailed == null ? 43 : hashFailed.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CollectionProgressExecutionVO(state=" + this.getState() + ", replayed=" + this.isReplayed() + ", preview=" + this.getPreview() + ", succeeded=" + this.getSucceeded() + ", skipped=" + this.getSkipped() + ", failed=" + this.getFailed() + ")";
    }

    /**
     * 构造三个条目列表的独立空列表默认值
     * @return 新的空列表
     */
    private static List<CollectionProgressItemVO> defaultSucceeded() {
        return new ArrayList<>();
    }

    /**
     * 构造跳过条目列表的独立空列表默认值
     * @return 新的空列表
     */
    private static List<CollectionProgressFailureVO> defaultSkipped() {
        return new ArrayList<>();
    }

    /**
     * 构造失败条目列表的独立空列表默认值
     * @return 新的空列表
     */
    private static List<CollectionProgressFailureVO> defaultFailed() {
        return new ArrayList<>();
    }

    /**
     * {@code CollectionProgressExecutionVO} 的链式构建器
     *
     * <p>未显式设置的 {@code @Builder.Default} 字段在 {@link #build()} 时获得新的空列表，
     * 显式传入 {@code null} 则保持 {@code null}
     */
    public static class CollectionProgressExecutionVOBuilder {
        /** 执行状态 */
        private CollectionProgressState state;
        /** 是否为重复确认返回首次结果 */
        private boolean replayed;
        /** 预览变化时的新预览 */
        private CollectionProgressPreviewVO preview;
        /** 是否已显式设置成功条目 */
        private boolean succeededSet;
        /** 显式设置的成功条目 */
        private List<CollectionProgressItemVO> succeededValue;
        /** 是否已显式设置跳过条目 */
        private boolean skippedSet;
        /** 显式设置的跳过条目 */
        private List<CollectionProgressFailureVO> skippedValue;
        /** 是否已显式设置失败条目 */
        private boolean failedSet;
        /** 显式设置的失败条目 */
        private List<CollectionProgressFailureVO> failedValue;

        /**
         * 创建空构建器，三个列表字段保持未设置状态
         */
        CollectionProgressExecutionVOBuilder() {
        }

        /**
         * 设置执行状态，覆盖此前取值
         * @param state 执行状态，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressExecutionVO.CollectionProgressExecutionVOBuilder state(final CollectionProgressState state) {
            this.state = state;
            return this;
        }

        /**
         * 设置是否为重复确认返回首次结果，覆盖此前取值
         * @param replayed 重复确认且复用首次结果时为 {@code true}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressExecutionVO.CollectionProgressExecutionVOBuilder replayed(final boolean replayed) {
            this.replayed = replayed;
            return this;
        }

        /**
         * 设置预览变化时的新预览，覆盖此前取值
         * @param preview 新预览，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressExecutionVO.CollectionProgressExecutionVOBuilder preview(final CollectionProgressPreviewVO preview) {
            this.preview = preview;
            return this;
        }

        /**
         * 设置执行成功的条目列表，覆盖此前取值
         * @param succeeded 成功条目，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressExecutionVO.CollectionProgressExecutionVOBuilder succeeded(final List<CollectionProgressItemVO> succeeded) {
            this.succeededValue = succeeded;
            succeededSet = true;
            return this;
        }

        /**
         * 设置执行时跳过的条目列表，覆盖此前取值
         * @param skipped 跳过条目，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressExecutionVO.CollectionProgressExecutionVOBuilder skipped(final List<CollectionProgressFailureVO> skipped) {
            this.skippedValue = skipped;
            skippedSet = true;
            return this;
        }

        /**
         * 设置执行失败的条目列表，覆盖此前取值
         * @param failed 失败条目，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressExecutionVO.CollectionProgressExecutionVOBuilder failed(final List<CollectionProgressFailureVO> failed) {
            this.failedValue = failed;
            failedSet = true;
            return this;
        }

        /**
         * 构建执行结果，未设置的成功、跳过、失败列表各自获得新的空列表
         * @return 携带当前构建器取值的执行结果
         */
        public CollectionProgressExecutionVO build() {
            List<CollectionProgressItemVO> succeededValue = this.succeededValue;
            if (!this.succeededSet) succeededValue = CollectionProgressExecutionVO.defaultSucceeded();
            List<CollectionProgressFailureVO> skippedValue = this.skippedValue;
            if (!this.skippedSet) skippedValue = CollectionProgressExecutionVO.defaultSkipped();
            List<CollectionProgressFailureVO> failedValue = this.failedValue;
            if (!this.failedSet) failedValue = CollectionProgressExecutionVO.defaultFailed();
            return new CollectionProgressExecutionVO(this.state, this.replayed, this.preview, succeededValue, skippedValue, failedValue);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本，列表字段以 {@code ...Value} 形式展示
         */
        @Override
        public String toString() {
            return "CollectionProgressExecutionVO.CollectionProgressExecutionVOBuilder(state=" + this.state + ", replayed=" + this.replayed + ", preview=" + this.preview + ", succeededValue=" + this.succeededValue + ", skippedValue=" + this.skippedValue + ", failedValue=" + this.failedValue + ")";
        }
    }
}
