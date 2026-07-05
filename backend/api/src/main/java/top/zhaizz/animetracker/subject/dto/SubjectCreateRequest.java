package top.zhaizz.animetracker.subject.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 新增条目请求 DTO
 */
@Data
public class SubjectCreateRequest {

    private Integer bangumiId;

    @NotBlank(message = "条目名称不能为空")
    private String name;

    private String nameCn;
    private String summary;
    private Integer type;
    private Integer eps;
    private LocalDate airDate;
    private String image;
}
