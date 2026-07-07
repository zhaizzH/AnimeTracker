package top.zhaizz.subject.service;

import top.zhaizz.pojo.vo.EpisodeVO;

import java.util.List;

public interface EpisodeService {

    /** 按条目 ID 获取剧集列表（按 sort 升序） */
    List<EpisodeVO> getEpisodesBySubjectId(Long subjectId);
}
