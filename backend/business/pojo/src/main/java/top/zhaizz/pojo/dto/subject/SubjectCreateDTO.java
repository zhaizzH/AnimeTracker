package top.zhaizz.pojo.dto.subject;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDate;

/**
 * 新增条目请求 DTO
 */
@Data
public class SubjectCreateDTO {

    // DB 列为 NOT NULL UNIQUE，必填
    @NotNull(message = "Bangumi ID 不能为空")
    private Integer bangumiId;      // Bangumi API 条目ID

    @NotBlank(message = "条目名称不能为空")
    private String name;            // 日文/英文名

    private String nameCn;          // 中文名
    private String summary;         // 简介/描述
    private Integer type;           // 条目类型（2=动画）
    private Integer eps;            // 总集数
    private LocalDate airDate;      // 播出日期
    private String image;           // 封面图URL
}
