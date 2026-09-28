package top.zhaizz.client.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.springframework.stereotype.Service;
import top.zhaizz.client.converter.SubjectConverter;
import top.zhaizz.client.mapper.EpisodeMapper;
import top.zhaizz.client.mapper.SubjectMapper;
import top.zhaizz.client.service.EpisodeService;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.constant.ErrorType;
import top.zhaizz.pojo.entity.Episode;
import top.zhaizz.pojo.vo.subject.EpisodeVO;

import java.util.List;

/**
 * 剧集服务实现
 */
@Service
public class EpisodeServiceImpl implements EpisodeService {
    /**
     * 分集数据 Mapper
     */
    private final EpisodeMapper episodeMapper;
    /**
     * 条目数据 Mapper
     */
    private final SubjectMapper subjectMapper;

    /**
     * 注入分集与条目数据 Mapper
     * @param episodeMapper 提供分集查询的 Mapper，由 Spring 容器提供
     * @param subjectMapper 用于校验条目存在的 Mapper，由 Spring 容器提供
     */
    public EpisodeServiceImpl(final EpisodeMapper episodeMapper, final SubjectMapper subjectMapper) {
        this.episodeMapper = episodeMapper;
        this.subjectMapper = subjectMapper;
    }

    /** {@inheritDoc} */
    @Override
    public List<EpisodeVO> getEpisodesBySubjectId(Long subjectId) {
        if (subjectMapper.selectById(subjectId) == null) {
            throw new BizException(ErrorType.NOT_FOUND, "条目不存在");
        }

        List<Episode> episodes = episodeMapper.selectList(
                new LambdaQueryWrapper<Episode>()
                        .eq(Episode::getSubjectId, subjectId)
                        .orderByAsc(Episode::getSort)
        );
        return SubjectConverter.toEpisodeVOList(episodes);
    }
}
