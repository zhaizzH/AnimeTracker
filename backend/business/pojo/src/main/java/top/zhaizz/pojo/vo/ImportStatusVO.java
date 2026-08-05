package top.zhaizz.pojo.vo;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 导入状态信息 VO
 */
@Data
public class ImportStatusVO {

    private LocalDateTime lastImportedAt;   // 最近导入时间（从未导入=null）
    private Integer totalSubjects;          // 最近导入记录条数（最多 10 条）
    private List<ImportRecordVO> recentRecords; // 最近导入记录
}
