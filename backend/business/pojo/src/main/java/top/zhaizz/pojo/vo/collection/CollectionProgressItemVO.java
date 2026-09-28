package top.zhaizz.pojo.vo.collection;

/**
 * 收藏进度预览/执行明细项
 */
public class CollectionProgressItemVO {

    /** 条目ID */
    private Long subjectId; // 条目ID
    /** 条目名称 */
    private String subjectName; // 条目名称
    /** 当前进度 */
    private Integer currentEpStatus; // 当前进度
    /** 目标进度 */
    private Integer targetEpStatus; // 目标进度
    /** 更新后是否达到总集数 */
    private boolean completedAfterUpdate; // 更新后是否达到总集数
    /** 是否建议标记为看过 */
    private boolean suggestMarkAsWatched; // 是否建议标记为看过

    /** 创建字段均为默认值的空明细项 */
    public CollectionProgressItemVO() {
    }

    /**
     * 创建携带全部字段的明细项
     * @param subjectId 条目ID，可为 {@code null}
     * @param subjectName 条目名称，可为 {@code null}
     * @param currentEpStatus 操作前当前进度，可为 {@code null}
     * @param targetEpStatus 本次请求要推进到的目标进度，可为 {@code null}
     * @param completedAfterUpdate 更新后是否达到总集数
     * @param suggestMarkAsWatched 是否建议标记为看过
     */
    public CollectionProgressItemVO(final Long subjectId, final String subjectName, final Integer currentEpStatus, final Integer targetEpStatus, final boolean completedAfterUpdate, final boolean suggestMarkAsWatched) {
        this.subjectId = subjectId;
        this.subjectName = subjectName;
        this.currentEpStatus = currentEpStatus;
        this.targetEpStatus = targetEpStatus;
        this.completedAfterUpdate = completedAfterUpdate;
        this.suggestMarkAsWatched = suggestMarkAsWatched;
    }

    /**
     * 创建构建器，用于链式组装明细项
     * @return 空的明细项构建器
     */
    public static CollectionProgressItemVOBuilder builder() {
        return new CollectionProgressItemVOBuilder();
    }

    /**
     * 获取条目ID
     * @return 条目ID；未提供时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取条目名称
     * @return 条目名称；未提供时为 {@code null}
     */
    public String getSubjectName() {
        return this.subjectName;
    }

    /**
     * 获取当前进度
     * @return 操作前的剧集进度；未提供时为 {@code null}
     */
    public Integer getCurrentEpStatus() {
        return this.currentEpStatus;
    }

    /**
     * 获取目标进度
     * @return 本次请求期望推进到的剧集进度；未提供时为 {@code null}
     */
    public Integer getTargetEpStatus() {
        return this.targetEpStatus;
    }

    /**
     * 判断更新后是否达到总集数
     * @return 更新后本条目进度达到总集数时为 {@code true}
     */
    public boolean isCompletedAfterUpdate() {
        return this.completedAfterUpdate;
    }

    /**
     * 判断是否建议标记为看过
     * @return 建议将收藏标记为已看完时为 {@code true}
     */
    public boolean isSuggestMarkAsWatched() {
        return this.suggestMarkAsWatched;
    }

    /**
     * 替换条目ID
     * @param subjectId 条目ID，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换条目名称
     * @param subjectName 条目名称，可为 {@code null}
     */
    public void setSubjectName(final String subjectName) {
        this.subjectName = subjectName;
    }

    /**
     * 替换当前进度
     * @param currentEpStatus 操作前的剧集进度，可为 {@code null}
     */
    public void setCurrentEpStatus(final Integer currentEpStatus) {
        this.currentEpStatus = currentEpStatus;
    }

    /**
     * 替换目标进度
     * @param targetEpStatus 本次请求期望推进到的剧集进度，可为 {@code null}
     */
    public void setTargetEpStatus(final Integer targetEpStatus) {
        this.targetEpStatus = targetEpStatus;
    }

    /**
     * 替换更新后是否达到总集数的标记
     * @param completedAfterUpdate 更新后本条目进度达到总集数时为 {@code true}
     */
    public void setCompletedAfterUpdate(final boolean completedAfterUpdate) {
        this.completedAfterUpdate = completedAfterUpdate;
    }

    /**
     * 替换是否建议标记为看过的标记
     * @param suggestMarkAsWatched 建议将收藏标记为已看完时为 {@code true}
     */
    public void setSuggestMarkAsWatched(final boolean suggestMarkAsWatched) {
        this.suggestMarkAsWatched = suggestMarkAsWatched;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionProgressItemVO)) return false;
        final CollectionProgressItemVO other = (CollectionProgressItemVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.isCompletedAfterUpdate() != other.isCompletedAfterUpdate()) return false;
        if (this.isSuggestMarkAsWatched() != other.isSuggestMarkAsWatched()) return false;
        final Object thisSubjectId = this.getSubjectId();
        final Object otherSubjectId = other.getSubjectId();
        if (thisSubjectId == null ? otherSubjectId != null : !thisSubjectId.equals(otherSubjectId)) return false;
        final Object thisCurrentEpStatus = this.getCurrentEpStatus();
        final Object otherCurrentEpStatus = other.getCurrentEpStatus();
        if (thisCurrentEpStatus == null ? otherCurrentEpStatus != null : !thisCurrentEpStatus.equals(otherCurrentEpStatus)) return false;
        final Object thisTargetEpStatus = this.getTargetEpStatus();
        final Object otherTargetEpStatus = other.getTargetEpStatus();
        if (thisTargetEpStatus == null ? otherTargetEpStatus != null : !thisTargetEpStatus.equals(otherTargetEpStatus)) return false;
        final Object thisSubjectName = this.getSubjectName();
        final Object otherSubjectName = other.getSubjectName();
        if (thisSubjectName == null ? otherSubjectName != null : !thisSubjectName.equals(otherSubjectName)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CollectionProgressItemVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + (this.isCompletedAfterUpdate() ? 79 : 97);
        result = result * PRIME + (this.isSuggestMarkAsWatched() ? 79 : 97);
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
        final Object hashCurrentEpStatus = this.getCurrentEpStatus();
        result = result * PRIME + (hashCurrentEpStatus == null ? 43 : hashCurrentEpStatus.hashCode());
        final Object hashTargetEpStatus = this.getTargetEpStatus();
        result = result * PRIME + (hashTargetEpStatus == null ? 43 : hashTargetEpStatus.hashCode());
        final Object hashSubjectName = this.getSubjectName();
        result = result * PRIME + (hashSubjectName == null ? 43 : hashSubjectName.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CollectionProgressItemVO(subjectId=" + this.getSubjectId() + ", subjectName=" + this.getSubjectName() + ", currentEpStatus=" + this.getCurrentEpStatus() + ", targetEpStatus=" + this.getTargetEpStatus() + ", completedAfterUpdate=" + this.isCompletedAfterUpdate() + ", suggestMarkAsWatched=" + this.isSuggestMarkAsWatched() + ")";
    }

    /**
     * {@code CollectionProgressItemVO} 的链式构建器
     *
     * <p>全部字段均无默认值，未显式设置的字段保持 {@code null} 或类型零值
     */
    public static class CollectionProgressItemVOBuilder {
        /** 条目ID */
        private Long subjectId;
        /** 条目名称 */
        private String subjectName;
        /** 当前进度 */
        private Integer currentEpStatus;
        /** 目标进度 */
        private Integer targetEpStatus;
        /** 更新后是否达到总集数 */
        private boolean completedAfterUpdate;
        /** 是否建议标记为看过 */
        private boolean suggestMarkAsWatched;

        /**
         * 创建空构建器，全部字段保持未设置状态
         */
        CollectionProgressItemVOBuilder() {
        }

        /**
         * 设置条目ID，覆盖此前取值
         * @param subjectId 条目ID，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressItemVO.CollectionProgressItemVOBuilder subjectId(final Long subjectId) {
            this.subjectId = subjectId;
            return this;
        }

        /**
         * 设置条目名称，覆盖此前取值
         * @param subjectName 条目名称，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressItemVO.CollectionProgressItemVOBuilder subjectName(final String subjectName) {
            this.subjectName = subjectName;
            return this;
        }

        /**
         * 设置当前进度，覆盖此前取值
         * @param currentEpStatus 操作前的剧集进度，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressItemVO.CollectionProgressItemVOBuilder currentEpStatus(final Integer currentEpStatus) {
            this.currentEpStatus = currentEpStatus;
            return this;
        }

        /**
         * 设置目标进度，覆盖此前取值
         * @param targetEpStatus 本次请求期望推进到的剧集进度，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressItemVO.CollectionProgressItemVOBuilder targetEpStatus(final Integer targetEpStatus) {
            this.targetEpStatus = targetEpStatus;
            return this;
        }

        /**
         * 设置更新后是否达到总集数，覆盖此前取值
         * @param completedAfterUpdate 更新后本条目进度达到总集数时为 {@code true}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressItemVO.CollectionProgressItemVOBuilder completedAfterUpdate(final boolean completedAfterUpdate) {
            this.completedAfterUpdate = completedAfterUpdate;
            return this;
        }

        /**
         * 设置是否建议标记为看过，覆盖此前取值
         * @param suggestMarkAsWatched 建议将收藏标记为已看完时为 {@code true}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressItemVO.CollectionProgressItemVOBuilder suggestMarkAsWatched(final boolean suggestMarkAsWatched) {
            this.suggestMarkAsWatched = suggestMarkAsWatched;
            return this;
        }

        /**
         * 构建明细项
         * @return 携带当前构建器取值的明细项
         */
        public CollectionProgressItemVO build() {
            return new CollectionProgressItemVO(this.subjectId, this.subjectName, this.currentEpStatus, this.targetEpStatus, this.completedAfterUpdate, this.suggestMarkAsWatched);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "CollectionProgressItemVO.CollectionProgressItemVOBuilder(subjectId=" + this.subjectId + ", subjectName=" + this.subjectName + ", currentEpStatus=" + this.currentEpStatus + ", targetEpStatus=" + this.targetEpStatus + ", completedAfterUpdate=" + this.completedAfterUpdate + ", suggestMarkAsWatched=" + this.suggestMarkAsWatched + ")";
        }
    }
}
