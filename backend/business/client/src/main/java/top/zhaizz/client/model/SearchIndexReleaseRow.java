package top.zhaizz.client.model;

/**
 * 当前 MySQL 词法/向量双投影的发布指针
 */
public class SearchIndexReleaseRow {
    /**
     * 检索索引版本标识
     */
    private String indexVersion;
    /**
     * 检索配置版本标识
     */
    private String profileVersion;

    /** 创建字段均为默认值的空发布指针，供结果映射使用 */
    public SearchIndexReleaseRow() {
    }

    /**
     * 获取检索索引版本标识
     * @return 已发布的索引版本号，未设置时为 {@code null}
     */
    public String getIndexVersion() {
        return this.indexVersion;
    }

    /**
     * 获取检索配置版本标识
     * @return 已发布的检索配置版本号，未设置时为 {@code null}
     */
    public String getProfileVersion() {
        return this.profileVersion;
    }

    /**
     * 替换检索索引版本标识
     * @param indexVersion 新的索引版本号，可为 {@code null}
     */
    public void setIndexVersion(final String indexVersion) {
        this.indexVersion = indexVersion;
    }

    /**
     * 替换检索配置版本标识
     * @param profileVersion 新的检索配置版本号，可为 {@code null}
     */
    public void setProfileVersion(final String profileVersion) {
        this.profileVersion = profileVersion;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof SearchIndexReleaseRow)) return false;
        final SearchIndexReleaseRow other = (SearchIndexReleaseRow) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisIndexVersion = this.getIndexVersion();
        final Object otherIndexVersion = other.getIndexVersion();
        if (thisIndexVersion == null ? otherIndexVersion != null : !thisIndexVersion.equals(otherIndexVersion)) return false;
        final Object thisProfileVersion = this.getProfileVersion();
        final Object otherProfileVersion = other.getProfileVersion();
        if (thisProfileVersion == null ? otherProfileVersion != null : !thisProfileVersion.equals(otherProfileVersion)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof SearchIndexReleaseRow;
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
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "SearchIndexReleaseRow(indexVersion=" + this.getIndexVersion() + ", profileVersion=" + this.getProfileVersion() + ")";
    }
}
