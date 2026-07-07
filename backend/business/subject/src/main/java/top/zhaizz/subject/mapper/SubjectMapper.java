package top.zhaizz.subject.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.Subject;

import java.time.LocalDate;
import java.util.List;

/**
 * 条目 Mapper
 */
public interface SubjectMapper extends BaseMapper<Subject> {

    /**
     * 按关键词搜索（匹配 name 和 name_cn）
     */
    List<Subject> searchByKeyword(@Param("keyword") String keyword);

    /**
     * 按播出日期范围查询
     */
    List<Subject> findByAirDateRange(@Param("startDate") LocalDate startDate,
                                     @Param("endDate") LocalDate endDate);

    /**
     * 按标签名查询条目 ID 列表
     */
    List<Long> findSubjectIdsByTag(@Param("tagName") String tagName);
}
