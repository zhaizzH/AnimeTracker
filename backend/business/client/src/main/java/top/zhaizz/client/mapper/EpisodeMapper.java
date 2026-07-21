package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.Episode;
import java.util.List;

public interface EpisodeMapper extends BaseMapper<Episode> {
    List<Episode> findBySubjectIdOrderBySort(@Param("subjectId") Long subjectId);
}
