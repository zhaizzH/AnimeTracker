package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

import java.time.LocalDate;

/**
 * 日期计数行（内部聚合）
 */
@Data
public class DailyCountVO {
    /** 统计日期 */
    private LocalDate statDate;     // 统计日期
    /** 该日期数量 */
    private long cnt;               // 该日期数量
}
