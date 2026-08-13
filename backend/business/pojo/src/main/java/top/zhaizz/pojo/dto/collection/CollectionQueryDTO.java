package top.zhaizz.pojo.dto.collection;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

/** 收藏列表查询参数 */
@Data
public class CollectionQueryDTO {
    @Min(value = 1, message = "收藏类型范围 1-5")
    @Max(value = 5, message = "收藏类型范围 1-5")
    private Integer type;           // 收藏类型: 1=想看, 2=看过, 3=在看, 4=搁置, 5=抛弃

    @Min(value = 1, message = "页码不能小于1")
    private int page = 1;           // 页码

    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20;          // 每页条数
}
