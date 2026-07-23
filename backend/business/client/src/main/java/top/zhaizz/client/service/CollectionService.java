package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.CollectionUpdateDTO;
import top.zhaizz.pojo.vo.UserCollectionVO;

public interface CollectionService {

    PageResult<UserCollectionVO> listCollections(Long userId, Integer type, int page, int size);

    UserCollectionVO getCollection(Long userId, Long subjectId);

    void saveOrUpdate(Long userId, Long subjectId, CollectionUpdateDTO dto);

    void deleteCollection(Long userId, Long subjectId);

    void updateEpStatus(Long userId, Long subjectId, Integer epStatus);
}
