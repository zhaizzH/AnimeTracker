package top.zhaizz.pojo.dto.collection;

import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * 剧集进度更新请求 DTO
 */
@Data
public class EpisodeStatusDTO {
    @Min(value = 0, message = "剧集进度不能为负")
    private int epStatus;       // 看到第几集
}