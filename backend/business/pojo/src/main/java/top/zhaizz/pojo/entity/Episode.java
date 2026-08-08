package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 剧集实体
 */
@Data
@TableName("episode")
public class Episode {

    private Long id;                    // 剧集ID
    private Long subjectId;             // 所属条目ID
    private Integer bangumiEpId;        // Bangumi 剧集ID
    private Integer type;               // 剧集类型: 0=本篇, 1=SP, 2=OP, 3=ED, 4=预告
    private BigDecimal sort;            // 集数序号（支持小数点: 1, 1.5, 2 等）
    private String name;                // 日文/英文标题
    private String nameCn;              // 中文标题
    private String duration;            // 时长（如 "24m"）
    private LocalDate airdate;          // 播出日期
    private String description;         // 剧情简介
    private String status;              // 播出状态: Air=已播出, Today=今日播出, NA=未播出
    private LocalDateTime createdAt;    // 创建时间
}
