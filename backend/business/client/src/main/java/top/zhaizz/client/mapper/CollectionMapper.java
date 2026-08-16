package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.client.model.CollectionProgressCandidate;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.collection.UserCollectionSubjectVO;

import java.time.LocalDate;
import java.util.List;

/** 收藏 Mapper */
public interface CollectionMapper extends BaseMapper<UserCollection> {

    /** 查询当前用户本周区间内可推进的在看收藏与最新本篇集数 */
    List<CollectionProgressCandidate> selectProgressCandidates(
            @Param("userId") Long userId,
            @Param("weekStart") LocalDate weekStart,
            @Param("cutoffDate") LocalDate cutoffDate
    );

    /** 分页查询用户收藏列表（含番剧信息） */
    Page<UserCollectionSubjectVO> selectCollectionPage(
            Page<?> page,
            @Param("userId") Long userId,
            @Param("type") Integer type
    );

    /** 分页查询用户追番日程（含番剧信息，按季/周过滤） */
    Page<UserCollectionSubjectVO> selectSchedulePage(
            Page<?> page,
            @Param("userId") Long userId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate,
            @Param("weekday") Integer weekday
    );
}
