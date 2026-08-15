package top.zhaizz.client.model;

/**
 * 收藏进度预览快照内部状态（不直接暴露给 HTTP）
 */
public enum ProgressPreviewStatus {
    PENDING,        // 已生成，等待确认
    EXECUTING,      // 确认后正在执行
    COMPLETED,      // 执行完成
    FAILED,         // 执行失败
    INVALIDATED     // 数据变化已失效
}
