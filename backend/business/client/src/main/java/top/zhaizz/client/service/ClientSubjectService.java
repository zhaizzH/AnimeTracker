package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.dto.subject.SeasonQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectListQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectSearchQueryDTO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.subject.SubjectBatchResultVO;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.dto.subject.LexicalSearchRequestDTO;
import top.zhaizz.pojo.vo.subject.LexicalSearchResultVO;

import java.util.List;

/** 番剧查询服务接口 */
public interface ClientSubjectService {

    /**
     * 获取番剧列表（分页、排序）
     * @param request 条目分页及排序条件
     * @return 符合条件的条目分页
     */
    PageResult<SubjectListVO> listSubjects(SubjectListQueryDTO request);

    /**
     * 获取番剧详情
     * @param id 目标条目 ID
     * @return 条目详情及标签、关联展示数据
     * @throws top.zhaizz.common.exception.BizException 条目不存在时为 NOT_FOUND
     */
    SubjectDetailVO getSubjectDetail(Long id);

    /**
     * 搜索番剧（分页、多维筛选）
     * @param request 名称、标签和评分等搜索条件
     * @return 符合搜索条件的条目分页
     */
    PageResult<SubjectListVO> searchSubjects(SubjectSearchQueryDTO request);

    /**
     * 在 active search release 上执行受控 MySQL FULLTEXT 召回
     * @param request 词法检索词及候选过滤条件
     * @return 携带当前索引版本的词法候选列表
     * @throws top.zhaizz.common.exception.BizException 索引表未迁移或未发布时为 SERVICE_UNAVAILABLE
     */
    LexicalSearchResultVO lexicalSearch(LexicalSearchRequestDTO request);

    /**
     * 按季度筛选番剧（分页）
     * @param request 年份、季度和分页条件
     * @return 该季度的条目分页
     */
    PageResult<SubjectListVO> listBySeason(SeasonQueryDTO request);

    /**
     * 按周追番列表（分页）
     * @param request 年份、季度、星期及分页条件
     * @return 符合日程条件的分页结果
     */
    PageResult<SubjectListVO> listSchedule(ScheduleQueryDTO request);

    /**
     * 批量回查条目，并按可见性、收藏状态分类
     * @param subjectIds 待查询的条目 ID 列表
     * @param excludeCollected 是否排除该用户已收藏的条目
     * @param userId 所属用户 ID，由调用方确认访问权限
     * @return 按可见性与收藏状态分类的批量条目结果
     */
    SubjectBatchResultVO batch(List<Long> subjectIds, boolean excludeCollected, Long userId);

    /**
     * 库中实际存在的番剧年份（降序）
     * @return 库内条目年份，按降序排列
     */
    List<Integer> listYears();
}
