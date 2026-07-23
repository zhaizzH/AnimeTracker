package top.zhaizz.pojo.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.time.LocalDate;

/**
 * 新增条目请求 DTO
 */
@Data
public class SubjectCreateDTO {

    private Integer bangumiId;

    @NotBlank(message = "条目名称不能为空")
    private String name;

    private String nameCn;
    private String summary;
    private Integer type;           // 条目类型（2=动画）
    private Integer eps;            // 总集数
    private LocalDate airDate;
    private String image;
}
