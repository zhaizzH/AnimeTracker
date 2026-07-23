package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.CollectionUpdateDTO;
import top.zhaizz.pojo.vo.UserCollectionVO;

/** 收藏服务接口 */
public interface CollectionService {

    /** 获取用户收藏列表（分页） */
    PageResult<UserCollectionVO> listCollections(Long userId, Integer type, int page, int size);

    /** 获取用户对某番剧的收藏详情 */
    UserCollectionVO getCollection(Long userId, Long subjectId);

    /** 新增或修改收藏 */
    void saveOrUpdate(Long userId, Long subjectId, CollectionUpdateDTO dto);

    /** 删除收藏 */
    void deleteCollection(Long userId, Long subjectId);

    /** 更新剧集进度 */
    void updateEpStatus(Long userId, Long subjectId, Integer epStatus);
}
