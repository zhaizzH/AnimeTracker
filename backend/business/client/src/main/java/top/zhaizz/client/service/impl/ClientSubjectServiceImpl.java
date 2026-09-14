package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.support.SFunction;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.CollectionMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.model.LexicalSearchRow;
import top.zhaizz.client.model.SearchIndexReleaseRow;
import top.zhaizz.client.mapper.SubjectRelationMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.service.ClientSubjectService;
import top.zhaizz.client.util.SeasonUtil;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.client.converter.SubjectVoConverter;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.dto.subject.SeasonQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectListQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectSearchQueryDTO;
import top.zhaizz.pojo.dto.subject.LexicalSearchRequestDTO;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectRelation;
import top.zhaizz.pojo.entity.SubjectTag;

import top.zhaizz.pojo.vo.subject.SubjectBatchResultVO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.subject.SubjectRelationVO;
import top.zhaizz.pojo.vo.subject.LexicalSearchCandidateVO;
import top.zhaizz.pojo.vo.subject.LexicalSearchResultVO;

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
 * 番剧查询服务实现。
 */
@Service
@RequiredArgsConstructor
public class ClientSubjectServiceImpl implements ClientSubjectService {

    /**
     * 排序参数到列/字段的白名单。
     */
    private static final Map<String, SFunction<Subject, ?>> SORT_FIELDS = Map.of(
            "id", Subject::getId,
            "name", Subject::getName,
            "air_date", Subject::getAirDate,
            "rank", Subject::getRank,
            "collection_total", Subject::getCollectionTotal);
    /** 条目数据 Mapper。 */
    private final SubjectMapper subjectMapper;
    /** 条目标签关系 Mapper。 */
    private final SubjectTagMapper subjectTagMapper;
    /** 条目关联关系 Mapper。 */
    private final SubjectRelationMapper subjectRelationMapper;
    /** 收藏数据 Mapper。 */
    private final CollectionMapper collectionMapper;

    /** {@inheritDoc} */
    @Override
    public List<Integer> listYears() {
        return subjectMapper.selectYears();
    }

    /** {@inheritDoc} */
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

    /** {@inheritDoc} */
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

    /** {@inheritDoc} */
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

    /** {@inheritDoc} */
    @Override
    public LexicalSearchResultVO lexicalSearch(LexicalSearchRequestDTO request) {
        SearchIndexReleaseRow release;
        try {
            release = subjectMapper.selectActiveSearchIndexRelease();
        } catch (DataAccessException ex) {
            // A deployment that has not run migration-003 must fail closed as
            // an unavailable lexical index, never expose a 500 SQL detail.
            throw new BizException(ErrorType.SERVICE_UNAVAILABLE, "词法索引尚未迁移");
        }
        if (release == null || release.getIndexVersion() == null || release.getIndexVersion().isBlank()) {
            throw new BizException(ErrorType.SERVICE_UNAVAILABLE, "词法索引尚未发布");
        }

        List<Long> subjectIds = request.getSubjectIds() == null
                ? null
                : request.getSubjectIds().stream().distinct().toList();
        List<LexicalSearchRow> rows = subjectMapper.lexicalSearch(
                request.getQ().trim(), request.getTags(), request.getScoreMin(), request.getScoreMax(),
                request.getYear(), request.getWeekday(), subjectIds, release.getIndexVersion(), request.getLimit());

        List<LexicalSearchCandidateVO> candidates = new ArrayList<>();
        for (int i = 0; i < rows.size(); i++) {
            LexicalSearchRow row = rows.get(i);
            candidates.add(LexicalSearchCandidateVO.builder()
                    .subjectId(row.getSubjectId())
                    .name(row.getName())
                    .nameCn(row.getNameCn())
                    .lexicalScore(row.getLexicalScore())
                    .rank(i + 1)
                    .build());
        }
        return LexicalSearchResultVO.builder()
                .indexVersion(release.getIndexVersion())
                .profileVersion(release.getProfileVersion())
                .candidates(candidates)
                .build();
    }

    /** {@inheritDoc} */
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

    /** {@inheritDoc} */
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

    /** {@inheritDoc} */
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
                result.getItems().add(SubjectConverter.toBatchItemVO(subject));
            }
        }
        return result;
    }


    /**
     * 将受控排序字段转换为 MyBatis-Plus 的实体字段引用。
     *
     * @param sort 请求的排序字段
     * @return 允许的实体字段引用；不支持的字段返回默认评分字段
     */
    private SFunction<Subject, ?> buildSortField(String sort) {
        return SORT_FIELDS.getOrDefault(sort, Subject::getScore);
    }

    /**
     * 将受控排序字段转换为 SQL 白名单中的列名。
     *
     * @param sort 请求的排序字段
     * @return 安全的 SQL 列名
     */
    private String buildSortFieldRaw(String sort) {
        return "s." + (SORT_FIELDS.containsKey(sort) ? sort : "score");
    }

    /**
     * 将排序方向限制为 SQL 白名单中的升序或降序。
     *
     * @param order 请求的排序方向
     * @return {@code asc} 或 {@code desc}
     */
    private String buildOrderRaw(String order) {
        return "asc".equalsIgnoreCase(order) ? "asc" : "desc";
    }
}
