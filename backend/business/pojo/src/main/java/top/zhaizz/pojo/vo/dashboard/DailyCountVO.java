package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.time.LocalDate;

/**
 * 日期计数行（内部聚合）
 */
@Data
public class DailyCountVO {
    private LocalDate statDate;     // 统计日期
    private long cnt;               // 该日期数量
}
