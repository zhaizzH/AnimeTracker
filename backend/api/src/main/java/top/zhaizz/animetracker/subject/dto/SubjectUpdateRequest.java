package top.zhaizz.animetracker.subject.dto;

import lombok.Data;

import java.time.LocalDate;

/**
 * 编辑条目请求 DTO（所有字段可选）
 */
@Data
public class SubjectUpdateRequest {

    private String name;
    private String nameCn;
    private String summary;
    private Integer type;
    private Integer eps;
    private LocalDate airDate;
    private String image;
}
