package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

/** 番剧列表查询参数（排序字段进 SQL 走白名单，无注入风险） */
@Data
public class SubjectListQueryDTO {
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1;           // 页码

    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20;          // 每页条数

    private String sort = "score";  // 排序字段（score/rank/collection_total/...）

    private String order = "desc";  // 排序方向（asc/desc）
}
