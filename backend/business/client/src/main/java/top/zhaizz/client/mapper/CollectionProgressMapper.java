package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.client.model.CollectionProgressCandidate;
import top.zhaizz.pojo.entity.UserCollection;

import java.time.LocalDate;
import java.util.List;

/** 收藏进度候选 Mapper */
public interface CollectionProgressMapper extends BaseMapper<UserCollection> {

    /** 查询当前用户本周区间内可推进的在看收藏与最新本篇集数 */
    List<CollectionProgressCandidate> selectCandidates(
            @Param("userId") Long userId,
            @Param("weekStart") LocalDate weekStart,
            @Param("cutoffDate") LocalDate cutoffDate
    );
}
