package top.zhaizz.client.model;

/**
 * 收藏进度预览快照内部状态（不直接暴露给 HTTP）。
 */
public enum ProgressPreviewStatus {
    /** 预览已生成，等待用户确认。 */
    PENDING,
    /** 已获得执行权，正在推进收藏进度。 */
    EXECUTING,
    /** 已保存执行结果，可供幂等重放。 */
    COMPLETED,
    /** 数据发生变化，原预览不可再执行。 */
    INVALIDATED
}
