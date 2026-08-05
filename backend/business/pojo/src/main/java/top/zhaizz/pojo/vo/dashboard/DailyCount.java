package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.time.LocalDate;

/**
 * 日期计数行（内部聚合）
 */
@Data
public class DailyCount {
    private LocalDate statDate;
    private long cnt;
}
