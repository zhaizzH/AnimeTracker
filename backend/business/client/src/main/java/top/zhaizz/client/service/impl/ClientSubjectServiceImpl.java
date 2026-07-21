package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.support.SFunction;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.EpisodeMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.service.ClientSubjectService;
import top.zhaizz.client.util.SeasonUtil;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.pojo.vo.EpisodeVO;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.SubjectListVO;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ClientSubjectServiceImpl implements ClientSubjectService {

    private final SubjectMapper subjectMapper;
    private final EpisodeMapper episodeMapper;
    private final SubjectTagMapper subjectTagMapper;

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

        return SubjectConverter.toSubjectDetailVO(subject, SubjectConverter.toTagVOList(tags));
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
    public PageResult<SubjectListVO> searchSubjects(String keyword, int page, int size) {
        List<Subject> records = subjectMapper.searchByKeyword(keyword);

        int total = records.size();
        int startIndex = (page - 1) * size;
        int endIndex = Math.min(startIndex + size, total);

        List<Subject> pageRecords;
        if (startIndex >= total) {
            pageRecords = List.of();
        } else {
            pageRecords = records.subList(startIndex, endIndex);
        }

        return PageResult.of(
                pageRecords.stream()
                        .map(SubjectConverter::toSubjectListVO)
                        .collect(Collectors.toList()),
                total,
                page,
                size
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
}
