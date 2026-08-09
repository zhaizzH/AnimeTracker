package top.zhaizz.pojo.vo;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 导入状态信息 VO
 */
@Data
public class ImportStatusVO {

    private LocalDateTime lastImportedAt;   // 条目导入时间（从未导入=null）
    private Integer totalSubjects;          // 条目总数（subject 表计数）
    private List<ImportRecordVO> recentRecords; // 条目导入记录
}
