package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.Subject;
import java.time.LocalDate;
import java.util.List;

public interface SubjectMapper extends BaseMapper<Subject> {
    List<Subject> searchByKeyword(@Param("keyword") String keyword);
    List<Subject> findByAirDateRange(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate);
    List<Long> findSubjectIdsByTag(@Param("tagName") String tagName);
    List<Subject> findByAirDateRangeAndWeekday(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate, @Param("weekday") Integer weekday);
}
