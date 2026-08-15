package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import top.zhaizz.client.converter.CollectionConverter;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.service.CollectionService;
import top.zhaizz.client.util.SeasonUtil;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.collection.CollectionQueryDTO;
import top.zhaizz.pojo.dto.collection.CollectionUpdateDTO;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import java.time.LocalDate;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.collection.UserCollectionSubjectVO;
import top.zhaizz.pojo.vo.collection.UserCollectionVO;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * 收藏服务实现
 */
@Service
@RequiredArgsConstructor
public class CollectionServiceImpl implements CollectionService {

    private final CollectionMapper collectionMapper;
    private final SubjectMapper subjectMapper;

    @Override
    public PageResult<UserCollectionVO> listCollections(Long userId, CollectionQueryDTO request) {
        Page<UserCollectionSubjectVO> mpPage = collectionMapper.selectCollectionPage(
                new Page<>(request.getPage(), request.getSize()), userId, request.getType());

        return PageResult.of(
                CollectionConverter.toUserCollectionVOList(mpPage.getRecords()),
                mpPage.getTotal(),
                (int) mpPage.getCurrent(),
                (int) mpPage.getSize()
        );
    }

    @Override
    public Map<Integer, Long> listCounts(Long userId) {
        QueryWrapper<UserCollection> qw = new QueryWrapper<>();
        qw.select("type", "COUNT(*) AS count").eq("user_id", userId).groupBy("type");
        List<Map<String, Object>> rows = collectionMapper.selectMaps(qw);
        Map<Integer, Long> counts = new HashMap<>();
        for (Map<String, Object> row : rows) {
            counts.put(((Number) row.get("type")).intValue(), ((Number) row.get("count")).longValue());
        }
        return counts;
    }

    @Override
    public UserCollectionVO getCollection(Long userId, Long subjectId) {
        UserCollection collection = collectionMapper.selectOne(
                new LambdaQueryWrapper<UserCollection>()
                        .eq(UserCollection::getUserId, userId)
                        .eq(UserCollection::getSubjectId, subjectId));
        if (collection == null) return null;

        return toSimpleVO(collection);
    }

    @Override
    @Transactional
    public void saveOrUpdate(Long userId, Long subjectId, CollectionUpdateDTO request) {
        if (subjectMapper.selectById(subjectId) == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        UserCollection existing = collectionMapper.selectOne(
                new LambdaQueryWrapper<UserCollection>()
                        .eq(UserCollection::getUserId, userId)
                        .eq(UserCollection::getSubjectId, subjectId));

        // 仅当完全无变化的重复提交（同类型且评分/进度均未改动）才视为冲突返回 409；修改评分、进度或换类型都是合法更新
        if (existing != null
                && Objects.equals(existing.getType(), request.getType())
                && (request.getRate() == null || Objects.equals(existing.getRate(), request.getRate()))
                && (request.getEpStatus() == null || Objects.equals(existing.getEpStatus(), request.getEpStatus()))) {
            throw new BizException(ErrorType.CONFLICT, "该条目已收藏，请勿重复收藏");
        }

        if (existing == null) {
            UserCollection entity = new UserCollection();
            entity.setUserId(userId);
            entity.setSubjectId(subjectId);
            entity.setType(request.getType());
            entity.setRate(request.getRate() != null ? request.getRate() : 0);
            entity.setEpStatus(request.getEpStatus() != null ? request.getEpStatus() : 0);
            entity.setCreatedAt(java.time.LocalDateTime.now());
            entity.setUpdatedAt(entity.getCreatedAt());
            collectionMapper.insert(entity);
        } else {
            existing.setType(request.getType());
            if (request.getRate() != null) existing.setRate(request.getRate());
            if (request.getEpStatus() != null) existing.setEpStatus(request.getEpStatus());
            existing.setUpdatedAt(java.time.LocalDateTime.now());
            collectionMapper.updateById(existing);
        }
    }

    @Override
    public void deleteCollection(Long userId, Long subjectId) {
        int affected = collectionMapper.delete(
                new LambdaQueryWrapper<UserCollection>()
                        .eq(UserCollection::getUserId, userId)
                        .eq(UserCollection::getSubjectId, subjectId));
        if (affected == 0) {
            throw new BizException(ErrorType.NOT_FOUND, "收藏记录不存在");
        }
    }

    @Override
    public void updateEpStatus(Long userId, Long subjectId, Integer epStatus) {
        UserCollection collection = collectionMapper.selectOne(
                new LambdaQueryWrapper<UserCollection>()
                        .eq(UserCollection::getUserId, userId)
                        .eq(UserCollection::getSubjectId, subjectId));
        if (collection == null) {
            throw new BizException(ErrorType.NOT_FOUND, "收藏记录不存在");
        }
        collection.setEpStatus(epStatus);
        collection.setUpdatedAt(java.time.LocalDateTime.now());
        collectionMapper.updateById(collection);
    }

    @Override
    public PageResult<UserCollectionVO> listSchedule(Long userId, ScheduleQueryDTO request) {
        int year = request.getYear() != null ? request.getYear() : SeasonUtil.getCurrentYear();
        String quarter = request.getQuarter() != null ? request.getQuarter() : SeasonUtil.getCurrentQuarter();
        Integer weekday = request.getWeekday() == -1 ? null : request.getWeekday();
        LocalDate[] range = SeasonUtil.getSeasonRange(year, quarter);
        Page<UserCollectionSubjectVO> mpPage = collectionMapper.selectSchedulePage(
                new Page<>(request.getPage(), request.getSize()), userId, range[0], range[1], weekday);

        return PageResult.of(
                CollectionConverter.toUserCollectionVOList(mpPage.getRecords()),
                mpPage.getTotal(),
                (int) mpPage.getCurrent(),
                (int) mpPage.getSize()
        );
    }

    private UserCollectionVO toSimpleVO(UserCollection entity) {
        UserCollectionVO vo = new UserCollectionVO();
        vo.setId(entity.getId());
        vo.setSubjectId(entity.getSubjectId());
        vo.setType(entity.getType());
        vo.setRate(entity.getRate());
        vo.setEpStatus(entity.getEpStatus());
        return vo;
    }
}
