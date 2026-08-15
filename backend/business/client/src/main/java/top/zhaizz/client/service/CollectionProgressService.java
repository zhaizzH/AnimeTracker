package top.zhaizz.client.service;

import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;

/**
 * 收藏进度预览服务接口
 */
public interface CollectionProgressService {

    /** 生成当前用户本周周一至昨日可推进的追番进度预览 */
    CollectionProgressPreviewVO createPreview(Long userId);
}
