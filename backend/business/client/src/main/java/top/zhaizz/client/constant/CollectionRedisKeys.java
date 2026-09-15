package top.zhaizz.client.constant;

/** 客户端收藏进度预览使用的 Redis 键前缀 */
public final class CollectionRedisKeys {
    /**
     * 禁止实例化仅提供静态操作的工具类
     */
    private CollectionRedisKeys() {
    }

    /** 进度预览数据 */
    public static final String PROGRESS_PREVIEW = "collection:progress-preview:";
    /** 进度预览互斥锁 */
    public static final String PROGRESS_LOCK = "collection:progress-lock:";
}
