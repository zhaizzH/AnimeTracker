package top.zhaizz.pojo.dto.subject;

import lombok.Data;

import java.time.LocalDate;

/**
 * 编辑条目请求 DTO（所有字段可选）
 */
@Data
public class SubjectUpdateDTO {

    /** 日文/英文名 */
    private String name;            // 日文/英文名
    /** 中文名 */
    private String nameCn;          // 中文名
    /** 简介/描述 */
    private String summary;         // 简介/描述
    /** 条目类型（2=动画） */
    private Integer type;           // 条目类型（2=动画）
    /** 总集数 */
    private Integer eps;            // 总集数
    /** 播出日期 */
    private LocalDate airDate;      // 播出日期
    /** 封面图URL */
    private String image;           // 封面图URL
}
