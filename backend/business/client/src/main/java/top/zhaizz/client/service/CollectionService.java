package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.collection.CollectionQueryDTO;
import top.zhaizz.pojo.dto.collection.CollectionUpdateDTO;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.vo.collection.UserCollectionVO;

import java.util.Map;

/** 收藏服务接口 */
public interface CollectionService {

    /** 获取用户收藏列表（分页） */
    PageResult<UserCollectionVO> listCollections(Long userId, CollectionQueryDTO request);

    /** 获取用户各收藏类型计数（key=type 1-5） */
    Map<Integer, Long> listCounts(Long userId);

    /** 获取用户对某番剧的收藏详情 */
    UserCollectionVO getCollection(Long userId, Long subjectId);

    /** 新增或修改收藏 */
    void saveOrUpdate(Long userId, Long subjectId, CollectionUpdateDTO dto);

    /** 删除收藏 */
    void deleteCollection(Long userId, Long subjectId);

    /** 更新剧集进度 */
    void updateEpStatus(Long userId, Long subjectId, Integer epStatus);

    /** 获取用户追番日程（分页，按季/周过滤） */
    PageResult<UserCollectionVO> listSchedule(Long userId, ScheduleQueryDTO request);
}
