package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.support.SFunction;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.mapper.SubjectRelationMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.service.ClientSubjectService;
import top.zhaizz.client.util.SeasonUtil;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.converter.SubjectVoConverter;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.dto.subject.SeasonQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectListQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectSearchQueryDTO;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectRelation;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.subject.SubjectBatchItemVO;
import top.zhaizz.pojo.vo.subject.SubjectBatchResultVO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.subject.SubjectRelationVO;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 番剧查询服务实现
 */
@Service
@RequiredArgsConstructor
public class ClientSubjectServiceImpl implements ClientSubjectService {

    /**
     * 排序参数到列/字段的白名单
     */
    private static final Map<String, SFunction<Subject, ?>> SORT_FIELDS = Map.of(
            "id", Subject::getId,
            "name", Subject::getName,
            "air_date", Subject::getAirDate,
            "rank", Subject::getRank,
            "collection_total", Subject::getCollectionTotal);
    private final SubjectMapper subjectMapper;
    private final SubjectTagMapper subjectTagMapper;
    private final SubjectRelationMapper subjectRelationMapper;
    private final CollectionMapper collectionMapper;

    @Override
    public List<Integer> listYears() {
        return subjectMapper.selectYears();
    }

    @Override
    public PageResult<SubjectListVO> listSubjects(SubjectListQueryDTO request) {
        LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
                .orderBy(true, "asc".equals(buildOrderRaw(request.getOrder())), buildSortField(request.getSort()));

        Page<Subject> mpPage = subjectMapper.selectPage(new Page<>(request.getPage(), request.getSize()), wrapper);

        return PageResult.of(
                mpPage.getRecords().stream()
                        .map(SubjectConverter::toSubjectListVO)
                        .collect(Collectors.toList()),
                mpPage.getTotal(),
                (int) mpPage.getCurrent(),
                (int) mpPage.getSize()
        );
    }

    @Override
    public SubjectDetailVO getSubjectDetail(Long id) {
        Subject subject = subjectMapper.selectById(id);
        if (subject == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        List<SubjectTag> tags = subjectTagMapper.selectList(
                new LambdaQueryWrapper<SubjectTag>().eq(SubjectTag::getSubjectId, id)
        );

        SubjectDetailVO detailVO = SubjectVoConverter.toSubjectDetailVO(subject, SubjectVoConverter.toTagVOList(tags));

        // 组装关联条目（一次批量查询替代 N+1，保持顺序与 null 过滤语义）
        List<SubjectRelation> relations = subjectRelationMapper.selectList(
                new LambdaQueryWrapper<SubjectRelation>().eq(SubjectRelation::getSubjectId, id)
        );
        List<Long> relatedIds = relations.stream()
                .map(SubjectRelation::getRelatedSubjectId)
                .distinct()
                .toList();
        Map<Long, Subject> relatedById = relatedIds.isEmpty() ? Map.of()
                : subjectMapper.selectBatchIds(relatedIds).stream()
                .collect(Collectors.toMap(Subject::getId, s -> s));
        List<SubjectRelationVO> relationVOs = relations.stream()
                .map(rel -> SubjectConverter.toSubjectRelationVO(rel, relatedById.get(rel.getRelatedSubjectId())))
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
        detailVO.setRelations(relationVOs);

        return detailVO;
    }

    @Override
    public PageResult<SubjectListVO> searchSubjects(SubjectSearchQueryDTO request) {
        String keyword = (request.getQ() != null && !request.getQ().trim().isEmpty()) ? request.getQ().trim() : null;
        String sortField = buildSortFieldRaw(request.getSort());
        String orderDir = buildOrderRaw(request.getOrder());

        IPage<Subject> mpPage = subjectMapper.searchWithFilters(
                new Page<>(request.getPage(), request.getSize()),
                keyword, request.getTag(), request.getScoreMin(), request.getScoreMax(),
                request.getYear(), request.getWeekday(), sortField, orderDir);

        return PageResult.of(
                mpPage.getRecords().stream()
                        .map(SubjectConverter::toSubjectListVO)
                        .collect(Collectors.toList()),
                mpPage.getTotal(),
                (int) mpPage.getCurrent(),
                (int) mpPage.getSize()
        );
    }

    @Override
    public PageResult<SubjectListVO> listBySeason(SeasonQueryDTO request) {
        LocalDate[] range = SeasonUtil.getSeasonRange(request.getYear(), request.getQuarter());
        LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
                .between(Subject::getAirDate, range[0], range[1])
                .orderByAsc(Subject::getAirDate);

        Page<Subject> mpPage = subjectMapper.selectPage(new Page<>(request.getPage(), request.getSize()), wrapper);

        return PageResult.of(
                mpPage.getRecords().stream()
                        .map(SubjectConverter::toSubjectListVO)
                        .collect(Collectors.toList()),
                mpPage.getTotal(),
                (int) mpPage.getCurrent(),
                (int) mpPage.getSize()
        );
    }

    @Override
    public PageResult<SubjectListVO> listSchedule(ScheduleQueryDTO request) {
        int year = request.getYear() != null ? request.getYear() : SeasonUtil.getCurrentYear();
        String quarter = request.getQuarter() != null ? request.getQuarter() : SeasonUtil.getCurrentQuarter();
        Integer weekday = request.getWeekday() == -1 ? null : request.getWeekday();
        LocalDate[] range = SeasonUtil.getSeasonRange(year, quarter);
        LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
                .between(Subject::getAirDate, range[0], range[1])
                .orderByAsc(Subject::getAirWeekday)
                .orderByDesc(Subject::getScore);

        if (weekday != null && weekday >= 0 && weekday <= 6) {
            wrapper.eq(Subject::getAirWeekday, weekday);
        }

        Page<Subject> mpPage = subjectMapper.selectPage(new Page<>(request.getPage(), request.getSize()), wrapper);

        return PageResult.of(
                mpPage.getRecords().stream()
                        .map(SubjectConverter::toSubjectListVO)
                        .collect(Collectors.toList()),
                mpPage.getTotal(),
                (int) mpPage.getCurrent(),
                (int) mpPage.getSize()
        );
    }

    @Override
    public SubjectBatchResultVO batch(List<Long> subjectIds, boolean excludeCollected, Long userId) {
        List<Long> uniqueIds = new ArrayList<>(new LinkedHashSet<>(subjectIds));
        Map<Long, Subject> subjectsById = subjectMapper.selectBatchIds(uniqueIds).stream()
                .collect(Collectors.toMap(Subject::getId, subject -> subject));
        Set<Long> collectedIds = excludeCollected && userId != null
                ? new HashSet<>(collectionMapper.findCollectedSubjectIds(userId, uniqueIds))
                : Set.of();

        SubjectBatchResultVO result = new SubjectBatchResultVO();
        for (Long id : uniqueIds) {
            Subject subject = subjectsById.get(id);
            if (subject == null) {
                result.getMissingIds().add(id);
            } else if (!Integer.valueOf(2).equals(subject.getType()) || Boolean.TRUE.equals(subject.getNsfw())) {
                result.getFilteredIds().add(id);
            } else if (collectedIds.contains(id)) {
                result.getCollectedIds().add(id);
            } else {
                result.getItems().add(toBatchItemVO(subject));
            }
        }
        return result;
    }

    private SubjectBatchItemVO toBatchItemVO(Subject subject) {
        SubjectBatchItemVO item = new SubjectBatchItemVO();
        item.setId(subject.getId());
        item.setName(subject.getName());
        item.setNameCn(subject.getNameCn());
        item.setImage(subject.getImage());
        item.setScore(subject.getScore());
        item.setRatingTotal(subject.getRatingTotal());
        item.setCollectionTotal(subject.getCollectionTotal());
        item.setAirDate(subject.getAirDate());
        item.setType(subject.getType());
        item.setNsfw(subject.getNsfw());
        return item;
    }

    private SFunction<Subject, ?> buildSortField(String sort) {
        return SORT_FIELDS.getOrDefault(sort, Subject::getScore);
    }

    private String buildSortFieldRaw(String sort) {
        return "s." + (SORT_FIELDS.containsKey(sort) ? sort : "score");
    }

    private String buildOrderRaw(String order) {
        return "asc".equalsIgnoreCase(order) ? "asc" : "desc";
    }
}
