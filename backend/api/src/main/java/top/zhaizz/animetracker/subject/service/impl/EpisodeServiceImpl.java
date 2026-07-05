package top.zhaizz.animetracker.subject.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.animetracker.common.exception.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.subject.converter.SubjectConverter;
import top.zhaizz.animetracker.common.entity.Episode;
import top.zhaizz.animetracker.subject.mapper.EpisodeMapper;
import top.zhaizz.animetracker.subject.mapper.SubjectMapper;
import top.zhaizz.animetracker.subject.service.EpisodeService;
import top.zhaizz.animetracker.common.vo.EpisodeVO;

import java.util.List;

@Service
@RequiredArgsConstructor
public class EpisodeServiceImpl implements EpisodeService {

    private final EpisodeMapper episodeMapper;
    private final SubjectMapper subjectMapper;

    @Override
    public List<EpisodeVO> getEpisodesBySubjectId(Long subjectId) {
        if (subjectMapper.selectById(subjectId) == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        List<Episode> episodes = episodeMapper.findBySubjectIdOrderBySort(subjectId);
        return SubjectConverter.toEpisodeVOList(episodes);
    }
}
