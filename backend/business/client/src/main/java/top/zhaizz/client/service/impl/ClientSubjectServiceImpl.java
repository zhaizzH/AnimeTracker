package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.support.SFunction;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.mapper.SubjectRelationMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.service.ClientSubjectService;
import top.zhaizz.client.util.SeasonUtil;
import top.zhaizz.common.converter.SubjectVoConverter;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectRelation;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectListQueryDTO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.subject.SubjectRelationVO;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 番剧查询服务实现
 */
@Service
@RequiredArgsConstructor
public class ClientSubjectServiceImpl implements ClientSubjectService {

    private final SubjectMapper subjectMapper;
    private final SubjectTagMapper subjectTagMapper;
    private final SubjectRelationMapper subjectRelationMapper;

    @Override
    public PageResult<SubjectListVO> listSubjects(SubjectListQueryDTO request) {
        LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
                .orderBy(true, "asc".equalsIgnoreCase(request.getOrder()), buildSortField(request.getSort()));

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
        List<SubjectRelation> relations = subjectRelationMapper.findBySubjectId(id);
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
    public PageResult<SubjectListVO> searchSubjects(String keyword, int page, int size,
            List<String> tagList, BigDecimal scoreMin, BigDecimal scoreMax,
            Integer year, Integer weekday, String sort, String order) {

        String sortField = buildSortFieldRaw(sort);
        String orderDir = buildOrderRaw(order);

        IPage<Subject> mpPage = subjectMapper.searchWithFilters(
                new Page<>(page, size),
                keyword, tagList, scoreMin, scoreMax, year, weekday,
                sortField, orderDir);

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
    public PageResult<SubjectListVO> listBySeason(int year, String quarter, int page, int size) {
        LocalDate[] range = SeasonUtil.getSeasonRange(year, quarter);
        LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
                .between(Subject::getAirDate, range[0], range[1])
                .orderByAsc(Subject::getAirDate);

        Page<Subject> mpPage = subjectMapper.selectPage(new Page<>(page, size), wrapper);

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

    private SFunction<Subject, ?> buildSortField(String sort) {
        return switch (sort) {
            case "id" -> Subject::getId;
            case "name" -> Subject::getName;
            case "air_date" -> Subject::getAirDate;
            case "rank" -> Subject::getRank;
            case "collection_total" -> Subject::getCollectionTotal;
            default -> Subject::getScore;
        };
    }

    private String buildSortFieldRaw(String sort) {
        return switch (sort) {
            case "id" -> "s.id";
            case "name" -> "s.name";
            case "air_date" -> "s.air_date";
            case "rank" -> "s.rank";
            case "collection_total" -> "s.collection_total";
            default -> "s.score";
        };
    }

    private String buildOrderRaw(String order) {
        return "asc".equalsIgnoreCase(order) ? "asc" : "desc";
    }
}
