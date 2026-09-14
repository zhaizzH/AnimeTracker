package top.zhaizz.pojo.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;
/**
 * 导入记录实体。
 */
@Data
@TableName("import_record")
public class ImportRecord {
    /** 记录ID。 */
    private Long id;                    // 记录ID
    /** 导入模式: full, recent, season, since。 */
    private String mode;                // 导入模式: full, recent, season, since
    /** 季度标识（如 2026-spring）。 */
    private String seasonKey;           // 季度标识（如 2026-spring）
    /** 开始时间。 */
    private LocalDateTime startedAt;    // 开始时间
    /** 完成时间。 */
    private LocalDateTime completedAt;  // 完成时间
    /** 状态: RUNNING, COMPLETED, FAILED。 */
    private String status;              // 状态: RUNNING, COMPLETED, FAILED
    /** 本次导入的条目数。 */
    private int subjectCount;           // 本次导入的条目数
    /** 错误信息（失败时记录）。 */
    private String errorMessage;        // 错误信息（失败时记录）
    /** 导入断点 JSON。 */
    private String checkpointJson;      // 导入断点 JSON
    /** 已扫描条目数。 */
    private Integer scannedCount;       // 已扫描条目数
    /** 成功处理条目数。 */
    private Integer successCount;       // 成功处理条目数
    /** 失败处理条目数。 */
    private Integer failureCount;       // 失败处理条目数
    /** 跳过条目数。 */
    private Integer skippedCount;       // 跳过条目数
    /** 源数据快照时间。 */
    private LocalDateTime sourceSnapshotAt; // 源数据快照时间
    /** 最近任务心跳时间。 */
    private LocalDateTime heartbeatAt;  // 最近任务心跳时间
    /** 创建时间。 */
    private LocalDateTime createdAt;    // 创建时间
}
