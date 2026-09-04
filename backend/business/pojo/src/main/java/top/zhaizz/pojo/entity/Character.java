package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 动漫角色实体（角色/作品内组织）
 * 注意: 类名为 Character，与 java.lang.Character 同名，使用时请通过包名 top.zhaizz.pojo.entity.Character 区分
 */
@Data
@TableName("character")
public class Character {

    private Long id;                        // 角色ID
    private Integer bangumiCharacterId;     // Bangumi 角色ID
    private String characterType;           // 角色类型: CHARACTER=角色, ORGANIZATION=作品内组织
    private String name;                    // 名称
    private String summary;                 // 简介
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
