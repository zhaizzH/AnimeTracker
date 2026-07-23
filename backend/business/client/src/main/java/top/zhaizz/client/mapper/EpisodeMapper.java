package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.Episode;
import java.util.List;

/** 剧集 Mapper */
public interface EpisodeMapper extends BaseMapper<Episode> {
    /** 根据条目 ID 查询剧集列表（按 sort 升序） */
    List<Episode> findBySubjectIdOrderBySort(@Param("subjectId") Long subjectId);
}
