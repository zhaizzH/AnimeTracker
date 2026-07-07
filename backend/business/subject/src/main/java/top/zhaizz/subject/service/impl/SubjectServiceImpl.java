package top.zhaizz.subject.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.support.SFunction;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.subject.converter.SubjectConverter;
import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.entity.SubjectTag;
import top.zhaizz.subject.mapper.EpisodeMapper;
import top.zhaizz.subject.mapper.SubjectMapper;
import top.zhaizz.subject.mapper.SubjectTagMapper;
import top.zhaizz.subject.service.SubjectService;
import top.zhaizz.subject.util.SeasonUtil;
import top.zhaizz.pojo.vo.EpisodeVO;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.SubjectListVO;
import top.zhaizz.pojo.vo.TagVO;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class SubjectServiceImpl implements SubjectService {

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
        List<TagVO> tagVOs = SubjectConverter.toTagVOList(tags);

        return SubjectConverter.toSubjectDetailVO(subject, tagVOs);
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
    @Transactional
    public SubjectDetailVO createSubject(SubjectCreateDTO request) {
        if (request.getBangumiId() != null) {
            Long count = subjectMapper.selectCount(
                    new LambdaQueryWrapper<Subject>().eq(Subject::getBangumiId, request.getBangumiId())
            );
            if (count > 0) {
                throw new BizException(ErrorType.CONFLICT, "该 Bangumi 条目已存在");
            }
        }

        Subject subject = SubjectConverter.toEntityFromCreate(request);
        subject.setNsfw(false);
        subject.setImportStatus(0);
        subject.setCreatedAt(LocalDateTime.now());
        subject.setUpdatedAt(LocalDateTime.now());

        subjectMapper.insert(subject);
        return getSubjectDetail(subject.getId());
    }

    @Override
    @Transactional
    public SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request) {
        Subject subject = subjectMapper.selectById(id);
        if (subject == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        SubjectConverter.updateFromRequest(subject, request);
        subject.setUpdatedAt(LocalDateTime.now());
        subjectMapper.updateById(subject);

        return getSubjectDetail(id);
    }

    @Override
    @Transactional
    public void deleteSubject(Long id) {
        Subject subject = subjectMapper.selectById(id);
        if (subject == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        subjectMapper.deleteById(id);
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
