package top.zhaizz.pojo.vo.collection;

/**
 * 收藏进度执行跳过/失败项
 */
public class CollectionProgressFailureVO {

    /** 条目ID */
    private Long subjectId; // 条目ID
    /** 条目名称 */
    private String subjectName; // 条目名称
    /** 当前进度 */
    private Integer currentEpStatus; // 当前进度
    /** 目标进度 */
    private Integer targetEpStatus; // 目标进度
    /** 跳过/失败原因 */
    private String reason; // 跳过/失败原因

    /** 创建字段均为默认值的空条目 */
    public CollectionProgressFailureVO() {
    }

    /**
     * 创建携带全部字段的跳过/失败项
     * @param subjectId 条目ID，可为 {@code null}
     * @param subjectName 条目名称，可为 {@code null}
     * @param currentEpStatus 操作前当前进度，可为 {@code null}
     * @param targetEpStatus 本次请求要推进到的目标进度，可为 {@code null}
     * @param reason 跳过或失败原因，可为 {@code null}
     */
    public CollectionProgressFailureVO(final Long subjectId, final String subjectName, final Integer currentEpStatus, final Integer targetEpStatus, final String reason) {
        this.subjectId = subjectId;
        this.subjectName = subjectName;
        this.currentEpStatus = currentEpStatus;
        this.targetEpStatus = targetEpStatus;
        this.reason = reason;
    }

    /**
     * 创建构建器，用于链式组装跳过/失败项
     * @return 空的跳过/失败项构建器
     */
    public static CollectionProgressFailureVOBuilder builder() {
        return new CollectionProgressFailureVOBuilder();
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
     * 获取跳过/失败原因
     * @return 跳过或失败的文字说明；未提供时为 {@code null}
     */
    public String getReason() {
        return this.reason;
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
     * 替换跳过/失败原因
     * @param reason 跳过或失败的文字说明，可为 {@code null}
     */
    public void setReason(final String reason) {
        this.reason = reason;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionProgressFailureVO)) return false;
        final CollectionProgressFailureVO other = (CollectionProgressFailureVO) o;
        if (!other.canEqual((Object) this)) return false;
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
        final Object thisReason = this.getReason();
        final Object otherReason = other.getReason();
        if (thisReason == null ? otherReason != null : !thisReason.equals(otherReason)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof CollectionProgressFailureVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashSubjectId = this.getSubjectId();
        result = result * PRIME + (hashSubjectId == null ? 43 : hashSubjectId.hashCode());
        final Object hashCurrentEpStatus = this.getCurrentEpStatus();
        result = result * PRIME + (hashCurrentEpStatus == null ? 43 : hashCurrentEpStatus.hashCode());
        final Object hashTargetEpStatus = this.getTargetEpStatus();
        result = result * PRIME + (hashTargetEpStatus == null ? 43 : hashTargetEpStatus.hashCode());
        final Object hashSubjectName = this.getSubjectName();
        result = result * PRIME + (hashSubjectName == null ? 43 : hashSubjectName.hashCode());
        final Object hashReason = this.getReason();
        result = result * PRIME + (hashReason == null ? 43 : hashReason.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "CollectionProgressFailureVO(subjectId=" + this.getSubjectId() + ", subjectName=" + this.getSubjectName() + ", currentEpStatus=" + this.getCurrentEpStatus() + ", targetEpStatus=" + this.getTargetEpStatus() + ", reason=" + this.getReason() + ")";
    }

    /**
     * {@code CollectionProgressFailureVO} 的链式构建器
     *
     * <p>所有字段均无默认值，未显式设置的字段保持 {@code null} 或类型零值
     */
    public static class CollectionProgressFailureVOBuilder {
        /** 条目ID */
        private Long subjectId;
        /** 条目名称 */
        private String subjectName;
        /** 当前进度 */
        private Integer currentEpStatus;
        /** 目标进度 */
        private Integer targetEpStatus;
        /** 跳过/失败原因 */
        private String reason;

        /**
         * 创建空构建器，全部字段保持未设置状态
         */
        CollectionProgressFailureVOBuilder() {
        }

        /**
         * 设置条目ID，覆盖此前取值
         * @param subjectId 条目ID，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressFailureVO.CollectionProgressFailureVOBuilder subjectId(final Long subjectId) {
            this.subjectId = subjectId;
            return this;
        }

        /**
         * 设置条目名称，覆盖此前取值
         * @param subjectName 条目名称，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressFailureVO.CollectionProgressFailureVOBuilder subjectName(final String subjectName) {
            this.subjectName = subjectName;
            return this;
        }

        /**
         * 设置当前进度，覆盖此前取值
         * @param currentEpStatus 操作前的剧集进度，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressFailureVO.CollectionProgressFailureVOBuilder currentEpStatus(final Integer currentEpStatus) {
            this.currentEpStatus = currentEpStatus;
            return this;
        }

        /**
         * 设置目标进度，覆盖此前取值
         * @param targetEpStatus 本次请求期望推进到的剧集进度，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressFailureVO.CollectionProgressFailureVOBuilder targetEpStatus(final Integer targetEpStatus) {
            this.targetEpStatus = targetEpStatus;
            return this;
        }

        /**
         * 设置跳过/失败原因，覆盖此前取值
         * @param reason 跳过或失败的文字说明，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public CollectionProgressFailureVO.CollectionProgressFailureVOBuilder reason(final String reason) {
            this.reason = reason;
            return this;
        }

        /**
         * 构建跳过/失败项
         * @return 携带当前构建器取值的跳过/失败项
         */
        public CollectionProgressFailureVO build() {
            return new CollectionProgressFailureVO(this.subjectId, this.subjectName, this.currentEpStatus, this.targetEpStatus, this.reason);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "CollectionProgressFailureVO.CollectionProgressFailureVOBuilder(subjectId=" + this.subjectId + ", subjectName=" + this.subjectName + ", currentEpStatus=" + this.currentEpStatus + ", targetEpStatus=" + this.targetEpStatus + ", reason=" + this.reason + ")";
        }
    }
}
