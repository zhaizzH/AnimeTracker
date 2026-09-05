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

    /** 获取番剧列表（分页、排序） */
    PageResult<SubjectListVO> listSubjects(SubjectListQueryDTO request);

    /** 获取番剧详情 */
    SubjectDetailVO getSubjectDetail(Long id);

    /** 搜索番剧（分页、多维筛选） */
    PageResult<SubjectListVO> searchSubjects(SubjectSearchQueryDTO request);

    /** 在 active search release 上执行受控 MySQL FULLTEXT 召回。 */
    LexicalSearchResultVO lexicalSearch(LexicalSearchRequestDTO request);

    /** 按季度筛选番剧（分页） */
    PageResult<SubjectListVO> listBySeason(SeasonQueryDTO request);

    /** 按周追番列表（分页） */
    PageResult<SubjectListVO> listSchedule(ScheduleQueryDTO request);

    /** 批量回查条目，并按可见性、收藏状态分类。 */
    SubjectBatchResultVO batch(List<Long> subjectIds, boolean excludeCollected, Long userId);

    /** 库中实际存在的番剧年份（降序） */
    List<Integer> listYears();
}
