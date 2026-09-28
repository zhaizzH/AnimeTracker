package top.zhaizz.pojo.vo.dashboard;

/**
 * 看板总览 VO
 */
public class DashboardOverviewVO {

    /** 用户总数 */
    private long userCount; // 用户总数
    /** 条目总数 */
    private long subjectCount; // 条目总数
    /** 收藏总数 */
    private long collectionCount; // 收藏总数
    /** 剧集总数 */
    private long episodeCount; // 剧集总数
    /** 导入记录总数 */
    private long importCount; // 导入记录总数
    /** 今日新增用户 */
    private long todayNewUsers; // 今日新增用户
    /** 今日新增收藏 */
    private long todayNewCollections; // 今日新增收藏
    /** 今日登录次数 */
    private long todayLogins; // 今日登录次数

    /** 创建各项计数均为零的空总览对象 */
    public DashboardOverviewVO() {
    }

    /**
     * 获取用户总数
     * @return 全站用户数量，未设置时为 {@code 0}
     */
    public long getUserCount() {
        return this.userCount;
    }

    /**
     * 获取条目总数
     * @return 全站条目数量，未设置时为 {@code 0}
     */
    public long getSubjectCount() {
        return this.subjectCount;
    }

    /**
     * 获取收藏总数
     * @return 全站收藏记录数量，未设置时为 {@code 0}
     */
    public long getCollectionCount() {
        return this.collectionCount;
    }

    /**
     * 获取剧集总数
     * @return 全站剧集数量，未设置时为 {@code 0}
     */
    public long getEpisodeCount() {
        return this.episodeCount;
    }

    /**
     * 获取导入记录总数
     * @return 导入记录数量，未设置时为 {@code 0}
     */
    public long getImportCount() {
        return this.importCount;
    }

    /**
     * 获取今日新增用户
     * @return 今日注册的用户数量，未设置时为 {@code 0}
     */
    public long getTodayNewUsers() {
        return this.todayNewUsers;
    }

    /**
     * 获取今日新增收藏
     * @return 今日新增的收藏数量，未设置时为 {@code 0}
     */
    public long getTodayNewCollections() {
        return this.todayNewCollections;
    }

    /**
     * 获取今日登录次数
     * @return 今日登录次数，未设置时为 {@code 0}
     */
    public long getTodayLogins() {
        return this.todayLogins;
    }

    /**
     * 替换用户总数
     * @param userCount 全站用户数量
     */
    public void setUserCount(final long userCount) {
        this.userCount = userCount;
    }

    /**
     * 替换条目总数
     * @param subjectCount 全站条目数量
     */
    public void setSubjectCount(final long subjectCount) {
        this.subjectCount = subjectCount;
    }

    /**
     * 替换收藏总数
     * @param collectionCount 全站收藏记录数量
     */
    public void setCollectionCount(final long collectionCount) {
        this.collectionCount = collectionCount;
    }

    /**
     * 替换剧集总数
     * @param episodeCount 全站剧集数量
     */
    public void setEpisodeCount(final long episodeCount) {
        this.episodeCount = episodeCount;
    }

    /**
     * 替换导入记录总数
     * @param importCount 导入记录数量
     */
    public void setImportCount(final long importCount) {
        this.importCount = importCount;
    }

    /**
     * 替换今日新增用户
     * @param todayNewUsers 今日注册的用户数量
     */
    public void setTodayNewUsers(final long todayNewUsers) {
        this.todayNewUsers = todayNewUsers;
    }

    /**
     * 替换今日新增收藏
     * @param todayNewCollections 今日新增的收藏数量
     */
    public void setTodayNewCollections(final long todayNewCollections) {
        this.todayNewCollections = todayNewCollections;
    }

    /**
     * 替换今日登录次数
     * @param todayLogins 今日登录次数
     */
    public void setTodayLogins(final long todayLogins) {
        this.todayLogins = todayLogins;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof DashboardOverviewVO)) return false;
        final DashboardOverviewVO other = (DashboardOverviewVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getUserCount() != other.getUserCount()) return false;
        if (this.getSubjectCount() != other.getSubjectCount()) return false;
        if (this.getCollectionCount() != other.getCollectionCount()) return false;
        if (this.getEpisodeCount() != other.getEpisodeCount()) return false;
        if (this.getImportCount() != other.getImportCount()) return false;
        if (this.getTodayNewUsers() != other.getTodayNewUsers()) return false;
        if (this.getTodayNewCollections() != other.getTodayNewCollections()) return false;
        if (this.getTodayLogins() != other.getTodayLogins()) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof DashboardOverviewVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashUserCount = this.getUserCount();
        result = result * PRIME + (int) (hashUserCount >>> 32 ^ hashUserCount);
        final long hashSubjectCount = this.getSubjectCount();
        result = result * PRIME + (int) (hashSubjectCount >>> 32 ^ hashSubjectCount);
        final long hashCollectionCount = this.getCollectionCount();
        result = result * PRIME + (int) (hashCollectionCount >>> 32 ^ hashCollectionCount);
        final long hashEpisodeCount = this.getEpisodeCount();
        result = result * PRIME + (int) (hashEpisodeCount >>> 32 ^ hashEpisodeCount);
        final long hashImportCount = this.getImportCount();
        result = result * PRIME + (int) (hashImportCount >>> 32 ^ hashImportCount);
        final long hashTodayNewUsers = this.getTodayNewUsers();
        result = result * PRIME + (int) (hashTodayNewUsers >>> 32 ^ hashTodayNewUsers);
        final long hashTodayNewCollections = this.getTodayNewCollections();
        result = result * PRIME + (int) (hashTodayNewCollections >>> 32 ^ hashTodayNewCollections);
        final long hashTodayLogins = this.getTodayLogins();
        result = result * PRIME + (int) (hashTodayLogins >>> 32 ^ hashTodayLogins);
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "DashboardOverviewVO(userCount=" + this.getUserCount() + ", subjectCount=" + this.getSubjectCount() + ", collectionCount=" + this.getCollectionCount() + ", episodeCount=" + this.getEpisodeCount() + ", importCount=" + this.getImportCount() + ", todayNewUsers=" + this.getTodayNewUsers() + ", todayNewCollections=" + this.getTodayNewCollections() + ", todayLogins=" + this.getTodayLogins() + ")";
    }
}
