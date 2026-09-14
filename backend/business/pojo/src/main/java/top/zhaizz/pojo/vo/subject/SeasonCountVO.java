package top.zhaizz.pojo.vo.subject;

import lombok.Data;

/**
 * 季度数量。
 */
@Data
public class SeasonCountVO {
    /** 季度标识（如 2026-summer）。 */
    private String seasonKey;   // 季度标识（如 2026-summer）
    /** 该季度条目数。 */
    private long count;         // 该季度条目数
}
