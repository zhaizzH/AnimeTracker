package top.zhaizz.pojo.vo.dashboard;

import java.time.LocalDate;

/**
 * 每日趋势点 VO
 */
public class TrendPointVO {

    /** 日期 */
    private LocalDate date; // 日期
    /** 当日新增用户 */
    private long newUsers; // 当日新增用户
    /** 当日新增收藏 */
    private long newCollections;// 当日新增收藏
    /** 当日登录次数 */
    private long logins; // 当日登录次数

    /** 创建各项计数均为零的空趋势点 */
    public TrendPointVO() {
    }

    /**
     * 获取日期
     * @return 趋势点对应日期；未提供时为 {@code null}
     */
    public LocalDate getDate() {
        return this.date;
    }

    /**
     * 获取当日新增用户
     * @return 当日注册的用户数量，未设置时为 {@code 0}
     */
    public long getNewUsers() {
        return this.newUsers;
    }

    /**
     * 获取当日新增收藏
     * @return 当日新增的收藏数量，未设置时为 {@code 0}
     */
    public long getNewCollections() {
        return this.newCollections;
    }

    /**
     * 获取当日登录次数
     * @return 当日登录次数，未设置时为 {@code 0}
     */
    public long getLogins() {
        return this.logins;
    }

    /**
     * 替换日期
     * @param date 趋势点对应日期，可为 {@code null}
     */
    public void setDate(final LocalDate date) {
        this.date = date;
    }

    /**
     * 替换当日新增用户
     * @param newUsers 当日注册的用户数量
     */
    public void setNewUsers(final long newUsers) {
        this.newUsers = newUsers;
    }

    /**
     * 替换当日新增收藏
     * @param newCollections 当日新增的收藏数量
     */
    public void setNewCollections(final long newCollections) {
        this.newCollections = newCollections;
    }

    /**
     * 替换当日登录次数
     * @param logins 当日登录次数
     */
    public void setLogins(final long logins) {
        this.logins = logins;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof TrendPointVO)) return false;
        final TrendPointVO other = (TrendPointVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getNewUsers() != other.getNewUsers()) return false;
        if (this.getNewCollections() != other.getNewCollections()) return false;
        if (this.getLogins() != other.getLogins()) return false;
        final Object thisDate = this.getDate();
        final Object otherDate = other.getDate();
        if (thisDate == null ? otherDate != null : !thisDate.equals(otherDate)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof TrendPointVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashNewUsers = this.getNewUsers();
        result = result * PRIME + (int) (hashNewUsers >>> 32 ^ hashNewUsers);
        final long hashNewCollections = this.getNewCollections();
        result = result * PRIME + (int) (hashNewCollections >>> 32 ^ hashNewCollections);
        final long hashLogins = this.getLogins();
        result = result * PRIME + (int) (hashLogins >>> 32 ^ hashLogins);
        final Object hashDate = this.getDate();
        result = result * PRIME + (hashDate == null ? 43 : hashDate.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "TrendPointVO(date=" + this.getDate() + ", newUsers=" + this.getNewUsers() + ", newCollections=" + this.getNewCollections() + ", logins=" + this.getLogins() + ")";
    }
}
