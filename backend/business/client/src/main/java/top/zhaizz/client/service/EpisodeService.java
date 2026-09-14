package top.zhaizz.client.service;

import top.zhaizz.pojo.vo.subject.EpisodeVO;

import java.util.List;

/**
 * 剧集服务接口。
 */
public interface EpisodeService {

    /**
     * 按条目 ID 获取剧集列表（按 sort 升序）。
     * @param subjectId 条目 ID
     * @return 按剧集序号升序排列的剧集列表
     * @throws top.zhaizz.common.exception.BizException 条目不存在时为 NOT_FOUND
     */
    List<EpisodeVO> getEpisodesBySubjectId(Long subjectId);
}
