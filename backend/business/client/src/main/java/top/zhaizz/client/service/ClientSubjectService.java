package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.EpisodeVO;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.SubjectListVO;

import java.util.List;

/** 番剧查询服务接口 */
public interface ClientSubjectService {

    /** 获取番剧列表（分页、排序） */
    PageResult<SubjectListVO> listSubjects(int page, int size, String sort, String order);

    /** 获取番剧详情 */
    SubjectDetailVO getSubjectDetail(Long id);

    /** 获取番剧剧集列表 */
    List<EpisodeVO> getEpisodes(Long subjectId);

    /** 搜索番剧（分页） */
    PageResult<SubjectListVO> searchSubjects(String keyword, int page, int size);

    /** 按季度筛选番剧（分页） */
    PageResult<SubjectListVO> listBySeason(int year, String quarter, int page, int size);

    /** 按周追番列表（分页） */
    PageResult<SubjectListVO> listSchedule(int year, String quarter, Integer weekday, int page, int size);
}
