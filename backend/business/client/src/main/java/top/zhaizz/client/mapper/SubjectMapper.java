package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.Subject;

import java.math.BigDecimal;
import java.util.List;

/**
 * 番剧 Mapper
 */
public interface SubjectMapper extends BaseMapper<Subject> {
    IPage<Subject> searchWithFilters(
            Page<?> page,
            @Param("keyword") String keyword,
            @Param("tagList") List<String> tagList,
            @Param("scoreMin") BigDecimal scoreMin,
            @Param("scoreMax") BigDecimal scoreMax,
            @Param("year") Integer year,
            @Param("weekday") Integer weekday,
            @Param("sortField") String sortField,
            @Param("order") String order);

    /**
     * 根据标签名查询番剧 ID 列表
     */
    List<Long> findSubjectIdsByTag(@Param("tagName") String tagName);
}
