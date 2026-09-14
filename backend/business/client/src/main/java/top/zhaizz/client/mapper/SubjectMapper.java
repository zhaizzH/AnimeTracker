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
 * 番剧 Mapper。
 */
public interface SubjectMapper extends BaseMapper<Subject> {
    /**
     * 多维条件搜索番剧（分页）：关键字/标签/评分/年份/周 + 排序。
     * @param page MyBatis 分页对象，包含当前页码与每页大小
     * @param keyword 名称检索关键词
     * @param tagList 筛选标签名称列表
     * @param scoreMin 最低评分筛选值
     * @param scoreMax 最高评分筛选值
     * @param year 年份筛选值
     * @param weekday 播出星期筛选值
     * @param sortField 调用方白名单校验后的 SQL 排序字段
     * @param order 调用方白名单校验后的排序方向
     * @return 匹配筛选条件的条目分页
     */
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
     * 根据标签名查询番剧 ID 列表。
     * @param tagName 用于匹配条目的标签名称
     * @return 匹配标签的条目 ID 列表
     */
    List<Long> findSubjectIdsByTag(@Param("tagName") String tagName);

    /**
     * 查询库中实际存在番剧年份（去重，降序）。
     * @return 库中实际存在番剧年份（去重，降序）
     */
    List<Integer> selectYears();

    /**
     * 读取唯一 active release；不存在时由 service fail-closed。
     * @return 当前激活的索引发布记录；不存在时为 null
     */
    SearchIndexReleaseRow selectActiveSearchIndexRelease();

    /**
     * 在指定 active release 的 SUBJECT 投影上执行参数化 FULLTEXT 召回。
     * @param query 查询条件
     * @param tags 条目标签列表
     * @param scoreMin 最低评分筛选值
     * @param scoreMax 最高评分筛选值
     * @param year 年份筛选值
     * @param weekday 播出星期筛选值
     * @param subjectIds 待查询的条目 ID 列表
     * @param indexVersion 当前索引发布版本
     * @param limit 最多返回的记录数
     * @return 指定版本中匹配过滤条件的候选查询行
     */
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
