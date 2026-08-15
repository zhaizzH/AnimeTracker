package top.zhaizz.client.service;

import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;

/**
 * 收藏进度预览服务接口
 */
public interface CollectionProgressService {

    /** 生成当前用户本周周一至昨日可推进的追番进度预览 */
    CollectionProgressPreviewVO createPreview(Long userId);

    /** 确认执行预览：重新校验，数据变化返回 PREVIEW_CHANGED，否则逐项执行并汇总 */
    CollectionProgressExecutionVO executePreview(Long userId, String previewId);
}
