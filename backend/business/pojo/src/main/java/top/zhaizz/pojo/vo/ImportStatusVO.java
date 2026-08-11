package top.zhaizz.pojo.vo;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 导入状态信息 VO
 */
@Data
public class ImportStatusVO {

    private LocalDateTime lastImportedAt;   // 最近一次导入完成时间（从未导入=null）
    private Long totalLogs;                 // 当前导入日志数量（import_record 全量）
    private Long completedCount;            // 历史成功任务总数（全量）
    private Long failedCount;               // 历史失败任务总数（全量）
    private List<ImportRecordVO> recentRecords; // 最近条目导入记录
}
