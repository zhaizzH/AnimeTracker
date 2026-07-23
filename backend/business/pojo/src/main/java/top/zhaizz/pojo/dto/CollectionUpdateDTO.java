package top.zhaizz.pojo.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * 追番收藏更新请求 DTO
 */
@Data
public class CollectionUpdateDTO {

    @NotNull(message = "收藏类型不能为空")
    @Min(value = 1, message = "收藏类型范围 1-5")
    @Max(value = 5, message = "收藏类型范围 1-5")
    private Integer type;           // 1=想看 2=看过 3=在看 4=搁置 5=抛弃

    @Min(value = 0, message = "评分范围 0-10")
    @Max(value = 10, message = "评分范围 0-10")
    private Integer rate;           // 0-10，0 未评分

    @Min(value = 0, message = "剧集进度不能为负")
    private Integer epStatus;
}
