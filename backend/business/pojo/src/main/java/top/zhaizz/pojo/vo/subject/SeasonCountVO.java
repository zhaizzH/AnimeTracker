package top.zhaizz.pojo.vo.subject;

import lombok.Data;

/**
 * 季度数量
 */
@Data
public class SeasonCountVO {
    private String seasonKey;   // 季度标识（如 2026-summer）
    private long count;         // 该季度条目数
}
