package top.zhaizz.pojo.dto;

import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * 剧集进度更新请求
 */
@Data
public class EpStatusDTO {
    @Min(value = 0, message = "剧集进度不能为负")
    private int epStatus;
}