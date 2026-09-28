package top.zhaizz.pojo.vo.subject;

import java.util.List;

/** 带 active release 版本的词法召回结果 */
public class LexicalSearchResultVO {
    /** 检索索引版本标识 */
    private String indexVersion;
    /** 检索配置版本标识 */
    private String profileVersion;
    /** 检索或证据候选列表 */
    private List<LexicalSearchCandidateVO> candidates;

    /** 创建字段均为默认值的空召回结果 */
    public LexicalSearchResultVO() {
    }

    /**
     * 创建携带全部字段的召回结果
     * @param indexVersion 检索索引版本标识，可为 {@code null}
     * @param profileVersion 检索配置版本标识，可为 {@code null}
     * @param candidates 检索或证据候选列表，可为 {@code null}；不进行复制
     */
    public LexicalSearchResultVO(final String indexVersion, final String profileVersion, final List<LexicalSearchCandidateVO> candidates) {
        this.indexVersion = indexVersion;
        this.profileVersion = profileVersion;
        this.candidates = candidates;
    }

    /**
     * 创建构建器，用于链式组装召回结果
     * @return 空的召回结果构建器
     */
    public static LexicalSearchResultVO.LexicalSearchResultVOBuilder builder() {
        return new LexicalSearchResultVO.LexicalSearchResultVOBuilder();
    }

    /**
     * 获取检索索引版本标识
     * @return 索引版本标识；未提供时为 {@code null}
     */
    public String getIndexVersion() {
        return this.indexVersion;
    }

    /**
     * 获取检索配置版本标识
     * @return 配置版本标识；未提供时为 {@code null}
     */
    public String getProfileVersion() {
        return this.profileVersion;
    }

    /**
     * 获取检索或证据候选列表
     * @return 候选列表；未提供时为 {@code null}
     */
    public List<LexicalSearchCandidateVO> getCandidates() {
        return this.candidates;
    }

    /**
     * 替换检索索引版本标识
     * @param indexVersion 索引版本标识，可为 {@code null}
     */
    public void setIndexVersion(final String indexVersion) {
        this.indexVersion = indexVersion;
    }

    /**
     * 替换检索配置版本标识
     * @param profileVersion 配置版本标识，可为 {@code null}
     */
    public void setProfileVersion(final String profileVersion) {
        this.profileVersion = profileVersion;
    }

    /**
     * 替换检索或证据候选列表
     * @param candidates 候选列表，可为 {@code null}；不进行复制
     */
    public void setCandidates(final List<LexicalSearchCandidateVO> candidates) {
        this.candidates = candidates;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LexicalSearchResultVO)) return false;
        final LexicalSearchResultVO other = (LexicalSearchResultVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisIndexVersion = this.getIndexVersion();
        final Object otherIndexVersion = other.getIndexVersion();
        if (thisIndexVersion == null ? otherIndexVersion != null : !thisIndexVersion.equals(otherIndexVersion)) return false;
        final Object thisProfileVersion = this.getProfileVersion();
        final Object otherProfileVersion = other.getProfileVersion();
        if (thisProfileVersion == null ? otherProfileVersion != null : !thisProfileVersion.equals(otherProfileVersion)) return false;
        final Object thisCandidates = this.getCandidates();
        final Object otherCandidates = other.getCandidates();
        if (thisCandidates == null ? otherCandidates != null : !thisCandidates.equals(otherCandidates)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof LexicalSearchResultVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashIndexVersion = this.getIndexVersion();
        result = result * PRIME + (hashIndexVersion == null ? 43 : hashIndexVersion.hashCode());
        final Object hashProfileVersion = this.getProfileVersion();
        result = result * PRIME + (hashProfileVersion == null ? 43 : hashProfileVersion.hashCode());
        final Object hashCandidates = this.getCandidates();
        result = result * PRIME + (hashCandidates == null ? 43 : hashCandidates.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "LexicalSearchResultVO(indexVersion=" + this.getIndexVersion() + ", profileVersion=" + this.getProfileVersion() + ", candidates=" + this.getCandidates() + ")";
    }

    /**
     * {@code LexicalSearchResultVO} 的链式构建器
     *
     * <p>各字段默认均为 {@code null}，未显式设置时构建结果对应字段保持 {@code null}
     */
    public static class LexicalSearchResultVOBuilder {
        /** 检索索引版本标识 */
        private String indexVersion;
        /** 检索配置版本标识 */
        private String profileVersion;
        /** 检索或证据候选列表 */
        private List<LexicalSearchCandidateVO> candidates;

        /** 创建字段均为未设置状态的空构建器 */
        LexicalSearchResultVOBuilder() {
        }

        /**
         * 设置检索索引版本标识，覆盖此前取值
         * @param indexVersion 索引版本标识，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchResultVO.LexicalSearchResultVOBuilder indexVersion(final String indexVersion) {
            this.indexVersion = indexVersion;
            return this;
        }

        /**
         * 设置检索配置版本标识，覆盖此前取值
         * @param profileVersion 配置版本标识，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchResultVO.LexicalSearchResultVOBuilder profileVersion(final String profileVersion) {
            this.profileVersion = profileVersion;
            return this;
        }

        /**
         * 设置检索或证据候选列表，覆盖此前取值
         * @param candidates 候选列表，可为 {@code null}；不进行复制
         * @return {@code this}，用于链式调用
         */
        public LexicalSearchResultVO.LexicalSearchResultVOBuilder candidates(final List<LexicalSearchCandidateVO> candidates) {
            this.candidates = candidates;
            return this;
        }

        /**
         * 构建召回结果，各字段取构建器当前取值
         * @return 携带当前构建器取值的召回结果
         */
        public LexicalSearchResultVO build() {
            return new LexicalSearchResultVO(this.indexVersion, this.profileVersion, this.candidates);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "LexicalSearchResultVO.LexicalSearchResultVOBuilder(indexVersion=" + this.indexVersion + ", profileVersion=" + this.profileVersion + ", candidates=" + this.candidates + ")";
        }
    }
}
