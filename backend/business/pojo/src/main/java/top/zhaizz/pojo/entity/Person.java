package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 人物/公司/组合实体
 */
@Data
@TableName("person")
public class Person {

    private Long id;                        // 人物ID
    private Integer bangumiPersonId;        // Bangumi 人物ID
    private String personType;              // 人物类型: PERSON=个人, COMPANY=公司, GROUP=组合（默认 PERSON）
    private String name;                    // 名称
    private String summary;                 // 简介
    private String careerJson;              // 职业 JSON（来自上游 infobox）
    private String infoboxJson;             // 完整 infobox JSON 快照
    private String image;                   // 图片URL
    private String imageSourceUrl;          // 原始图片 URL
    private String imageStorageStatus;      // 图片存储状态: PENDING/STORED/FAILED/ABSENT
    private String detailStatus;            // 详情状态: SUMMARY_ONLY/PENDING/COMPLETE/FAILED
    private String sourceHash;              // 来源数据哈希（用于变更检测）
    private LocalDateTime sourceFetchedAt;  // 最近成功抓取源详情时间
    private Long lastSeenImportId;          // 最近一次发现该实体的 import_record.id
    private Boolean sourceActive;           // 上游是否仍然活跃: 0=已失效, 1=活跃
    private LocalDateTime createdAt;        // 创建时间
    private LocalDateTime updatedAt;        // 更新时间
}
