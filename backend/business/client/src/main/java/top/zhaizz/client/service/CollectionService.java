package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.collection.CollectionQueryDTO;
import top.zhaizz.pojo.dto.collection.CollectionUpdateDTO;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.vo.collection.UserCollectionVO;
import top.zhaizz.pojo.vo.collection.WishlistAddResultVO;

import java.util.Map;

/** 收藏服务接口 */
public interface CollectionService {

    /**
     * 获取用户收藏列表（分页）
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param request 收藏状态筛选与分页条件
     * @return 指定用户的收藏分页，包含条目信息
     */
    PageResult<UserCollectionVO> listCollections(Long userId, CollectionQueryDTO request);

    /**
     * 获取用户各收藏类型计数（key=type 1-5）
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @return 实际存在的收藏状态到记录数的映射；无记录的状态不补零
     */
    Map<Integer, Long> listCounts(Long userId);

    /**
     * 仅当不存在收藏时加入想看（幂等，不覆盖已有收藏）
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param subjectId 条目 ID
     * @return 新增或已存在状态，不覆盖已有收藏
     * @throws top.zhaizz.common.exception.BizException 条目不存在时为 NOT_FOUND
     */
    WishlistAddResultVO addToWishlistIfAbsent(Long userId, Long subjectId);

    /**
     * 获取用户对某番剧的收藏详情
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param subjectId 条目 ID
     * @return 用户收藏详情，未收藏时返回 {@code null}
     */
    UserCollectionVO getCollection(Long userId, Long subjectId);

    /**
     * <p>创建时缺省评分和进度置 0；更新时空评分和进度保留原值，收藏类型始终覆盖
     * 新增或修改收藏
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param subjectId 条目 ID
     * @param request 收藏类型与可选评分、进度
     * @throws top.zhaizz.common.exception.BizException 条目不存在时为 NOT_FOUND，无变化的重复提交时为 CONFLICT
     */
    void saveOrUpdate(Long userId, Long subjectId, CollectionUpdateDTO request);

    /**
     * 删除收藏
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param subjectId 条目 ID
     * @throws top.zhaizz.common.exception.BizException 收藏记录不存在时为 NOT_FOUND
     */
    void deleteCollection(Long userId, Long subjectId);

    /**
     * 更新剧集进度
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param subjectId 条目 ID
     * @param epStatus 目标已看集数
     * @throws top.zhaizz.common.exception.BizException 收藏记录不存在时为 NOT_FOUND
     */
    void updateEpStatus(Long userId, Long subjectId, Integer epStatus);

    /**
     * 获取用户追番日程（分页，按季/周过滤）
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param request 年份、季度、星期及分页条件
     * @return 符合日程条件的分页结果
     */
    PageResult<UserCollectionVO> listSchedule(Long userId, ScheduleQueryDTO request);
}
