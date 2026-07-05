package top.zhaizz.animetracker.subject.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.animetracker.common.entity.Episode;

import java.util.List;

/**
 * 剧集 Mapper
 */
@Mapper
public interface EpisodeMapper extends BaseMapper<Episode> {

    /**
     * 按条目 ID 查询剧集列表（按 sort 升序）
     */
    List<Episode> findBySubjectIdOrderBySort(@Param("subjectId") Long subjectId);
}
