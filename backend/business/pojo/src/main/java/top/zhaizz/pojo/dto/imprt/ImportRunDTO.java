package top.zhaizz.pojo.dto.imprt;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/** 番剧导入触发参数（包名 imprt：import 为 Java 关键字不可作包名） */
@Data
public class ImportRunDTO {
    @NotBlank(message = "导入模式不能为空")
    @Pattern(regexp = "full|season|recent|since", message = "导入模式仅允许: full/season/recent/since")
    private String mode;        // 导入模式: full / season / recent / since

    private String key;         // 季度标识（season 模式必填），如 "2026-summer"

    private String since;       // 起始日期（since 模式必填），如 "2026-01-01"

    private Integer workers;    // 并发线程数，为空使用 Python 侧默认值
}
