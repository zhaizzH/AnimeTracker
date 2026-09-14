package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.client.model.CollectionProgressCandidate;
import top.zhaizz.pojo.entity.UserCollection;
import top.zhaizz.pojo.vo.collection.UserCollectionSubjectVO;

import java.time.LocalDate;
import java.util.List;

/** 收藏 Mapper。 */
public interface CollectionMapper extends BaseMapper<UserCollection> {

    /**
     * 查询当前用户本周区间内可推进的在看收藏与最新本篇集数。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param weekStart 统计周的起始日期
     * @param cutoffDate 统计截止日期
     * @return 统计日期范围内在看收藏的可推进集数
     */
    List<CollectionProgressCandidate> selectProgressCandidates(
            @Param("userId") Long userId,
            @Param("weekStart") LocalDate weekStart,
            @Param("cutoffDate") LocalDate cutoffDate
    );

    /**
     * 分页查询用户收藏列表（含番剧信息）。
     * @param page MyBatis 分页对象，包含当前页码与每页大小
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param type 收藏状态筛选值
     * @return 含条目信息的收藏分页
     */
    Page<UserCollectionSubjectVO> selectCollectionPage(
            Page<?> page,
            @Param("userId") Long userId,
            @Param("type") Integer type
    );

    /**
     * 分页查询用户追番日程（含番剧信息，按季/周过滤）。
     * @param page MyBatis 分页对象，包含当前页码与每页大小
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param startDate 筛选起始日期
     * @param endDate 筛选结束日期
     * @param weekday 播出星期筛选值
     * @return 按日期与星期过滤的收藏分页
     */
    Page<UserCollectionSubjectVO> selectSchedulePage(
            Page<?> page,
            @Param("userId") Long userId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate,
            @Param("weekday") Integer weekday
    );

    /**
     * 查询用户已收藏的指定条目。
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @param subjectIds 待查询的条目 ID 列表
     * @return 该用户已收藏的输入条目 ID
     */
    List<Long> findCollectedSubjectIds(
            @Param("userId") Long userId,
            @Param("subjectIds") List<Long> subjectIds
    );
}
