package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 导入记录统计
 */
@Data
public class ImportStatVO {
    private long importTotal;
    private long importSucceeded;
    private long importFailed;
}
