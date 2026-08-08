package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 导入记录统计
 */
@Data
public class ImportStatVO {
    private long importTotal;       // 导入总次数
    private long importSucceeded;   // 成功次数
    private long importFailed;      // 失败次数
}
