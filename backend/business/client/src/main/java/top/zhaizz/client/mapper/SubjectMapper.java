package top.zhaizz.client.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import top.zhaizz.pojo.entity.Subject;
import top.zhaizz.client.model.LexicalSearchRow;
import top.zhaizz.client.model.SearchIndexReleaseRow;

import java.math.BigDecimal;
import java.util.List;

/**
 * 番剧 Mapper
 */
public interface SubjectMapper extends BaseMapper<Subject> {
    /** 多维条件搜索番剧（分页）：关键字/标签/评分/年份/周 + 排序 */
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

    /** 查询库中实际存在番剧年份（去重，降序） */
    List<Integer> selectYears();

    /** 读取唯一 active release；不存在时由 service fail-closed。 */
    SearchIndexReleaseRow selectActiveSearchIndexRelease();

    /** 在指定 active release 的 SUBJECT 投影上执行参数化 FULLTEXT 召回。 */
    List<LexicalSearchRow> lexicalSearch(
            @Param("query") String query,
            @Param("tags") List<String> tags,
            @Param("scoreMin") BigDecimal scoreMin,
            @Param("scoreMax") BigDecimal scoreMax,
            @Param("year") Integer year,
            @Param("weekday") Integer weekday,
            @Param("subjectIds") List<Long> subjectIds,
            @Param("indexVersion") String indexVersion,
            @Param("limit") int limit);
}
