package top.zhaizz.animetracker.common.dto;

import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

/**
 * 搜索参数封装
 */
@Data
public class SubjectSearchCriteriaDTO {

    @NotEmpty(message = "搜索关键词不能为空")
    private String q;

    private int page = 1;

    private int size = 20;
}
