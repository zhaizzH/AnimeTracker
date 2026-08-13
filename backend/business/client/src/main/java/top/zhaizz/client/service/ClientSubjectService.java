package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectListQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectSearchQueryDTO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.subject.SubjectListVO;

/** 番剧查询服务接口 */
public interface ClientSubjectService {

    /** 获取番剧列表（分页、排序） */
    PageResult<SubjectListVO> listSubjects(SubjectListQueryDTO request);

    /** 获取番剧详情 */
    SubjectDetailVO getSubjectDetail(Long id);

    /** 搜索番剧（分页、多维筛选） */
    PageResult<SubjectListVO> searchSubjects(SubjectSearchQueryDTO request);

    /** 按季度筛选番剧（分页） */
    PageResult<SubjectListVO> listBySeason(int year, String quarter, int page, int size);

    /** 按周追番列表（分页） */
    PageResult<SubjectListVO> listSchedule(ScheduleQueryDTO request);
}
