package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 动漫条目实体
 */
@Data
@TableName("subject")
public class Subject {

    private Long id;                    // 条目ID
    private Integer bangumiId;          // Bangumi API 条目ID
    private String name;                // 日文/英文名
    private String nameCn;              // 中文名
    private String summary;             // 简介/描述
    private Integer type;               // 条目类型: 2=动画（本项目仅使用动画类型）
    private Integer eps;                // 总集数
    private Integer volumes;            // 总卷数
    private LocalDate airDate;          // 播出日期
    private Integer airWeekday;         // 播出星期（0=周日, 1=周一 ... 6=周六）
    private String image;               // 封面图URL
    private BigDecimal score;           // Bangumi 评分（0.0~10.0）
    @TableField("`rank`")
    private Integer rank;               // Bangumi 排名
    private Integer collectionTotal;    // 收藏数
    private Integer ratingTotal;        // 评分总人数
    private String ratingCountJson;     // 各评分人数 JSON
    private Integer collectionWish;     // 想看人数
    private Integer collectionCollect;  // 看过人数
    private Integer collectionDoing;    // 在看人数
    private Integer collectionOnHold;   // 搁置人数
    private Integer collectionDropped;  // 抛弃人数
    private String imageSourceUrl;      // 原始封面 URL
    private String imageStorageStatus;  // 封面存储状态
    private LocalDateTime imageCheckedAt; // 最近封面检查时间
    private LocalDateTime sourceFetchedAt; // 本系统最近成功抓取源详情时间
    private Boolean nsfw;               // 是否 NSFW: 0=否, 1=是
    private Integer importStatus;       // 导入状态: 0=待导入, 1=已导入
    private LocalDateTime lastImportedAt; // 最近导入时间
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
}
