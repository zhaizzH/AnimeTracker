package top.zhaizz.pojo.vo.collection;

/**
 * 本周追番进度预览/执行业务状态
 */
public enum CollectionProgressState {
    PENDING,            // 预览已生成，等待确认
    PREVIEW_CHANGED,    // 确认时数据已变化，返回新预览
    COMPLETED           // 执行完成（含部分成功）
}
