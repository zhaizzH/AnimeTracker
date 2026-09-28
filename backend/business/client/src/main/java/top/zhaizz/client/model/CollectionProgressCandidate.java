package top.zhaizz.client.model;

/**
 * 收藏进度候选项（聚合查询结果，非 HTTP 返回体）
 */
public class CollectionProgressCandidate {
    /**
     * 条目ID
     */
    private Long subjectId; // 条目ID
    /**
     * 条目名称
     */
    private String subjectName; // 条目名称
    /**
     * 当前进度
     */
    private Integer currentEpStatus; // 当前进度
    /**
     * 目标进度（本周区间内已播本篇最大整数集数）
     */
    private Integer targetEpStatus; // 目标进度（本周区间内已播本篇最大整数集数）
    /**
     * 总集数
     */
    private Integer totalEpisodes; // 总集数

    /** 创建全部字段为默认值的空候选项，供 Jackson 反序列化使用 */
    public CollectionProgressCandidate() {
    }

    /**
     * 创建携带全部字段的候选项
     * @param subjectId 条目ID，可为 {@code null}
     * @param subjectName 条目名称，可为 {@code null}
     * @param currentEpStatus 当前进度，可为 {@code null}
     * @param targetEpStatus 目标进度，可为 {@code null}
     * @param totalEpisodes 总集数，可为 {@code null}
     */
    public CollectionProgressCandidate(final Long subjectId, final String subjectName, final Integer currentEpStatus, final Integer targetEpStatus, final Integer totalEpisodes) {
        this.subjectId = subjectId;
        this.subjectName = subjectName;
        this.currentEpStatus = currentEpStatus;
        this.targetEpStatus = targetEpStatus;
        this.totalEpisodes = totalEpisodes;
    }

    /**
     * 创建候选项的链式构建器
     * @return 空的候选项构建器
     */
    public static CollectionProgressCandidate.CollectionProgressCandidateBuilder builder() {
        return new CollectionProgressCandidate.CollectionProgressCandidateBuilder();
    }

    /**
     * 收藏进度候选项的链式构建器
     */
    public static class CollectionProgressCandidateBuilder {
        /**
         * 条目ID
         */
        private Long subjectId;
        /**
         * 条目名称
         */
        private String subjectName;
        /**
         * 当前进度
         */
        private Integer currentEpStatus;
        /**
         * 目标进度（本周区间内已播本篇最大整数集数）
         */
        private Integer targetEpStatus;
        /**
         * 总集数
         */
        private Integer totalEpisodes;

        /** 创建字段均为默认值的空构建器 */
        CollectionProgressCandidateBuilder() {
        }

        /**
         * 设置条目ID
         * @param subjectId 条目ID，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public CollectionProgressCandidate.CollectionProgressCandidateBuilder subjectId(final Long subjectId) {
            this.subjectId = subjectId;
            return this;
        }

        /**
         * 设置条目名称
         * @param subjectName 条目名称，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public CollectionProgressCandidate.CollectionProgressCandidateBuilder subjectName(final String subjectName) {
            this.subjectName = subjectName;
            return this;
        }

        /**
         * 设置当前进度
         * @param currentEpStatus 当前进度，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public CollectionProgressCandidate.CollectionProgressCandidateBuilder currentEpStatus(final Integer currentEpStatus) {
            this.currentEpStatus = currentEpStatus;
            return this;
        }

        /**
         * 设置目标进度
         * @param targetEpStatus 目标进度，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public CollectionProgressCandidate.CollectionProgressCandidateBuilder targetEpStatus(final Integer targetEpStatus) {
            this.targetEpStatus = targetEpStatus;
            return this;
        }

        /**
         * 设置总集数
         * @param totalEpisodes 总集数，可为 {@code null}
         * @return {@code this} 以支持链式调用
         */
        public CollectionProgressCandidate.CollectionProgressCandidateBuilder totalEpisodes(final Integer totalEpisodes) {
            this.totalEpisodes = totalEpisodes;
            return this;
        }

        /**
         * 依据已设置的字段构建候选项实例
         * @return 使用构建器当前字段值的候选项
         */
        public CollectionProgressCandidate build() {
            return new CollectionProgressCandidate(this.subjectId, this.subjectName, this.currentEpStatus, this.targetEpStatus, this.totalEpisodes);
        }

        /**
         * 返回包含构建器全部字段的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "CollectionProgressCandidate.CollectionProgressCandidateBuilder(subjectId=" + this.subjectId + ", subjectName=" + this.subjectName + ", currentEpStatus=" + this.currentEpStatus + ", targetEpStatus=" + this.targetEpStatus + ", totalEpisodes=" + this.totalEpisodes + ")";
        }
    }

    /**
     * 获取条目ID
     * @return 收藏条目主键，未设置时为 {@code null}
     */
    public Long getSubjectId() {
        return this.subjectId;
    }

    /**
     * 获取条目名称
     * @return 条目展示名称，未设置时为 {@code null}
     */
    public String getSubjectName() {
        return this.subjectName;
    }

    /**
     * 获取当前进度
     * @return 已观看集数，未设置时为 {@code null}
     */
    public Integer getCurrentEpStatus() {
        return this.currentEpStatus;
    }

    /**
     * 获取目标进度
     * @return 本周区间内已播本篇最大整数集数，未设置时为 {@code null}
     */
    public Integer getTargetEpStatus() {
        return this.targetEpStatus;
    }

    /**
     * 获取总集数
     * @return 条目总集数，未设置时为 {@code null}
     */
    public Integer getTotalEpisodes() {
        return this.totalEpisodes;
    }

    /**
     * 替换条目ID
     * @param subjectId 新的条目主键，可为 {@code null}
     */
    public void setSubjectId(final Long subjectId) {
        this.subjectId = subjectId;
    }

    /**
     * 替换条目名称
     * @param subjectName 新的条目展示名称，可为 {@code null}
     */
    public void setSubjectName(final String subjectName) {
        this.subjectName = subjectName;
    }

    /**
     * 替换当前进度
     * @param currentEpStatus 新的已观看集数，可为 {@code null}
     */
    public void setCurrentEpStatus(final Integer currentEpStatus) {
        this.currentEpStatus = currentEpStatus;
    }

    /**
     * 替换目标进度
     * @param targetEpStatus 新的本周区间内已播本篇最大整数集数，可为 {@code null}
     */
    public void setTargetEpStatus(final Integer targetEpStatus) {
        this.targetEpStatus = targetEpStatus;
    }

    /**
     * 替换总集数
     * @param totalEpisodes 新的条目总集数，可为 {@code null}
     */
    public void setTotalEpisodes(final Integer totalEpisodes) {
        this.totalEpisodes = totalEpisodes;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof CollectionProgressCandidate)) return false;
        final CollectionProgressCandidate other = (CollectionProgressCandidate) o;
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
        final Object thisTotalEpisodes = this.getTotalEpisodes();
        final Object otherTotalEpisodes = other.getTotalEpisodes();
        if (thisTotalEpisodes == null ? otherTotalEpisodes != null : !thisTotalEpisodes.equals(otherTotalEpisodes)) return false;
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
        return other instanceof CollectionProgressCandidate;
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
        final Object hashTotalEpisodes = this.getTotalEpisodes();
        result = result * PRIME + (hashTotalEpisodes == null ? 43 : hashTotalEpisodes.hashCode());
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
        return "CollectionProgressCandidate(subjectId=" + this.getSubjectId() + ", subjectName=" + this.getSubjectName() + ", currentEpStatus=" + this.getCurrentEpStatus() + ", targetEpStatus=" + this.getTargetEpStatus() + ", totalEpisodes=" + this.getTotalEpisodes() + ")";
    }
}
