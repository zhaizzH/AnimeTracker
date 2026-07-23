package top.zhaizz.client.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.EpisodeMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.service.EpisodeService;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.vo.EpisodeVO;

import java.util.List;

/**
 * 剧集服务实现
 */
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
