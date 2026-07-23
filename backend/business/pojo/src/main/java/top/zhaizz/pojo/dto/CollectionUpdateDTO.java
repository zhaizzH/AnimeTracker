package top.zhaizz.pojo.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class CollectionUpdateDTO {

    @NotNull(message = "收藏类型不能为空")
    @Min(value = 1, message = "收藏类型范围 1-5")
    @Max(value = 5, message = "收藏类型范围 1-5")
    private Integer type;

    @Min(value = 0, message = "评分范围 0-10")
    @Max(value = 10, message = "评分范围 0-10")
    private Integer rate;

    @Min(value = 0, message = "剧集进度不能为负")
    private Integer epStatus;
}
