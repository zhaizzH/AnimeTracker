package top.zhaizz.pojo.vo.collection;

/**
 * 本周追番进度预览/执行业务状态
 */
public enum CollectionProgressState {
    /**
     * 预览已生成，等待用户确认
     */
    PENDING,
    /**
     * 确认时数据已变化，需要使用新预览
     */
    PREVIEW_CHANGED,
    /**
     * 进度执行完成，允许包含部分成功
     */
    COMPLETED
}
