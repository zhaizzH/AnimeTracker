package top.zhaizz.pojo.dto.imprt;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

/** 导入记录分页查询参数 */
@Data
public class ImportRecordQueryDTO {
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1;           // 页码

    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 1000, message = "每页条数不能超过1000")
    private int size = 10;          // 每页条数（导入记录量大，默认 10 上限 1000）

    private String status;          // 状态过滤：RUNNING / COMPLETED / FAILED，空表示全部
}
