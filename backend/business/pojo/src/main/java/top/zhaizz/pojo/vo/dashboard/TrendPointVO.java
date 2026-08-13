package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.time.LocalDate;

/**
 * 每日趋势点 VO
 */
@Data
public class TrendPointVO {
    private LocalDate date;     // 日期
    private long newUsers;      // 当日新增用户
    private long newCollections;// 当日新增收藏
    private long logins;        // 当日登录次数
}
