package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.mapper.SubjectTagMapper;
import top.zhaizz.client.service.TagService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.pojo.vo.SubjectListVO;
import top.zhaizz.pojo.vo.TagVO;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 标签服务实现
 */
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
                .toList();

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
