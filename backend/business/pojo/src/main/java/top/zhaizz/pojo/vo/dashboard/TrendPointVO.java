package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.time.LocalDate;

/**
 * 每日趋势点 VO
 */
@Data
public class TrendPointVO {
    private LocalDate date;
    private long newUsers;
    private long newCollections;
    private long logins;
}
