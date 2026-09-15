package top.zhaizz.client.service;

import top.zhaizz.pojo.vo.collection.CollectionProgressExecutionVO;
import top.zhaizz.pojo.vo.collection.CollectionProgressPreviewVO;

/**
 * 收藏进度预览服务接口
 */
public interface CollectionProgressService {

    /**
     * 生成当前用户本周周一至昨日可推进的追番进度预览
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @return 本周至昨日的进度预览，无可推进项时返回空预览
     */
    CollectionProgressPreviewVO createPreview(Long userId);

    /**
     * 确认执行预览：重新校验，数据变化返回 PREVIEW_CHANGED，否则逐项执行并汇总
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param previewId 已生成的进度预览标识
     * @return 预览变化提示或逐项执行结果，允许部分成功
     * @throws top.zhaizz.common.exception.BizException 预览不存在时为 NOT_FOUND；过期、状态无效或正在执行时为 CONFLICT
     */
    CollectionProgressExecutionVO executePreview(Long userId, String previewId);
}
