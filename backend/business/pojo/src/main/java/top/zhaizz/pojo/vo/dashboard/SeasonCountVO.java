package top.zhaizz.pojo.vo.dashboard;

import lombok.Data;

/**
 * 季度数量
 */
@Data
public class SeasonCountVO {
    private String seasonKey;   // 如 2026-summer
    private long count;
}
