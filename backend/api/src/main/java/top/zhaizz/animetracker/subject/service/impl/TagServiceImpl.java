package top.zhaizz.animetracker.subject.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.animetracker.common.PageResult;
import top.zhaizz.animetracker.subject.converter.SubjectConverter;
import top.zhaizz.animetracker.subject.entity.Subject;
import top.zhaizz.animetracker.subject.entity.SubjectTag;
import top.zhaizz.animetracker.subject.mapper.SubjectMapper;
import top.zhaizz.animetracker.subject.mapper.SubjectTagMapper;
import top.zhaizz.animetracker.subject.service.TagService;
import top.zhaizz.animetracker.subject.vo.SubjectListVO;
import top.zhaizz.animetracker.subject.vo.TagVO;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TagServiceImpl implements TagService {

    private final SubjectTagMapper subjectTagMapper;
    private final SubjectMapper subjectMapper;

    @Override
    public List<TagVO> listTags() {
        return subjectTagMapper.selectTagCountList().stream()
                .map(SubjectConverter::toTagVO)
                .collect(Collectors.toList());
    }

    @Override
    public PageResult<SubjectListVO> listSubjectsByTag(String tagName, int page, int size) {
        List<Long> subjectIds = subjectMapper.findSubjectIdsByTag(tagName);

        if (subjectIds.isEmpty()) {
            return PageResult.of(List.of(), 0, page, size);
        }

        int total = subjectIds.size();
        int startIndex = (page - 1) * size;
        int endIndex = Math.min(startIndex + size, total);

        List<Long> pageIds;
        if (startIndex >= total) {
            pageIds = List.of();
        } else {
            pageIds = subjectIds.subList(startIndex, endIndex);
        }

        List<Subject> subjects = subjectMapper.selectBatchIds(pageIds);
        List<Subject> sorted = pageIds.stream()
                .map(id -> subjects.stream().filter(s -> s.getId().equals(id)).findFirst().orElse(null))
                .filter(Objects::nonNull)
                .collect(Collectors.toList());

        return PageResult.of(
                sorted.stream()
                        .map(SubjectConverter::toSubjectListVO)
                        .collect(Collectors.toList()),
                total,
                page,
                size
        );
    }
}
