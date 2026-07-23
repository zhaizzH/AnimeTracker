package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.Subject;
import java.time.LocalDate;
import java.util.List;

/** 番剧 Mapper */
public interface SubjectMapper extends BaseMapper<Subject> {
    /** 根据关键词搜索番剧 */
    List<Subject> searchByKeyword(@Param("keyword") String keyword);
    /** 根据播出日期范围查询番剧 */
    List<Subject> findByAirDateRange(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate);
    /** 根据标签名查询番剧 ID 列表 */
    List<Long> findSubjectIdsByTag(@Param("tagName") String tagName);
    /** 根据播出日期范围和星期几查询番剧 */
    List<Subject> findByAirDateRangeAndWeekday(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate, @Param("weekday") Integer weekday);
}
