package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.support.SFunction;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.EpisodeMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.mapper.SubjectRelationMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.service.ClientSubjectService;
import top.zhaizz.client.util.SeasonUtil;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectRelation;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.EpisodeVO;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.SubjectListVO;
import top.zhaizz.pojo.vo.SubjectRelationVO;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 番剧查询服务实现
 */
@Service
@RequiredArgsConstructor
public class ClientSubjectServiceImpl implements ClientSubjectService {

    private final SubjectMapper subjectMapper;
    private final EpisodeMapper episodeMapper;
    private final SubjectTagMapper subjectTagMapper;
    private final SubjectRelationMapper subjectRelationMapper;

    @Override
    public PageResult<SubjectListVO> listSubjects(int page, int size, String sort, String order) {
        LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
                .orderBy(true, "asc".equalsIgnoreCase(order), buildSortField(sort));

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
    public SubjectDetailVO getSubjectDetail(Long id) {
        Subject subject = subjectMapper.selectById(id);
        if (subject == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        List<SubjectTag> tags = subjectTagMapper.selectList(
                new LambdaQueryWrapper<SubjectTag>().eq(SubjectTag::getSubjectId, id)
        );

        SubjectDetailVO detailVO = SubjectConverter.toSubjectDetailVO(subject, SubjectConverter.toTagVOList(tags));

        // 组装关联条目
        List<SubjectRelation> relations = subjectRelationMapper.findBySubjectId(id);
        List<SubjectRelationVO> relationVOs = relations.stream().map(rel -> {
            Subject related = subjectMapper.selectById(rel.getRelatedSubjectId());
            return SubjectConverter.toSubjectRelationVO(rel, related);
        }).filter(Objects::nonNull).collect(Collectors.toList());
        detailVO.setRelations(relationVOs);

        return detailVO;
    }

    @Override
    public List<EpisodeVO> getEpisodes(Long subjectId) {
        if (subjectMapper.selectById(subjectId) == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        List<Episode> episodes = episodeMapper.findBySubjectIdOrderBySort(subjectId);
        return SubjectConverter.toEpisodeVOList(episodes);
    }

    @Override
    public PageResult<SubjectListVO> searchSubjects(String keyword, int page, int size,
            List<String> tagList, BigDecimal scoreMin, BigDecimal scoreMax,
            Integer year, Integer weekday, String sort, String order) {

        String sortField = buildSortFieldRaw(sort);
        String orderDir = buildOrderRaw(order);

        Page<Subject> mpPage = subjectMapper.searchWithFilters(
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
    public PageResult<SubjectListVO> listSchedule(int year, String quarter, Integer weekday, int page, int size) {
        LocalDate[] range = SeasonUtil.getSeasonRange(year, quarter);
        LambdaQueryWrapper<Subject> wrapper = new LambdaQueryWrapper<Subject>()
                .between(Subject::getAirDate, range[0], range[1])
                .orderByAsc(Subject::getAirWeekday)
                .orderByDesc(Subject::getScore);

        if (weekday != null && weekday >= 0 && weekday <= 6) {
            wrapper.eq(Subject::getAirWeekday, weekday);
        }

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

    private SFunction<Subject, ?> buildSortField(String sort) {
        return switch (sort) {
            case "name" -> Subject::getName;
            case "air_date" -> Subject::getAirDate;
            case "rank" -> Subject::getRank;
            default -> Subject::getScore;
        };
    }

    private String buildSortFieldRaw(String sort) {
        return switch (sort) {
            case "name" -> "s.name";
            case "air_date" -> "s.air_date";
            case "rank" -> "s.rank";
            default -> "s.score";
        };
    }

    private String buildOrderRaw(String order) {
        return "asc".equalsIgnoreCase(order) ? "asc" : "desc";
    }
}
