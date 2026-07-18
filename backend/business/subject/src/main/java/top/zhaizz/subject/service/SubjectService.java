package top.zhaizz.subject.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.vo.EpisodeVO;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.SubjectListVO;

import java.util.List;

/**
 * 番剧服务接口
 */
public interface SubjectService {

    /** 分页条目列表（支持排序） */
    PageResult<SubjectListVO> listSubjects(int page, int size, String sort, String order);

    /** 条目详情（含标签） */
    SubjectDetailVO getSubjectDetail(Long id);

    /** 剧集列表 */
    List<EpisodeVO> getEpisodes(Long subjectId);

    /** 关键词搜索（分页） */
    PageResult<SubjectListVO> searchSubjects(String keyword, int page, int size);

    /** 按季度筛选（分页） */
    PageResult<SubjectListVO> listBySeason(int year, String quarter, int page, int size);

    /** 每周追番列表（按季度筛选 + 可选星期过滤） */
    PageResult<SubjectListVO> listSchedule(int year, String quarter, Integer weekday, int page, int size);

    /** 管理员 — 新增条目 */
    SubjectDetailVO createSubject(SubjectCreateDTO request);

    /** 管理员 — 编辑条目 */
    SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request);

    /** 管理员 — 删除条目 */
    void deleteSubject(Long id);
}
