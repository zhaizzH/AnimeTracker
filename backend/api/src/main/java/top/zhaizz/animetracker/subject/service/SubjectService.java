package top.zhaizz.animetracker.subject.service;

import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.common.dto.SubjectCreateDTO;
import top.zhaizz.animetracker.common.dto.SubjectUpdateDTO;
import top.zhaizz.animetracker.common.vo.EpisodeVO;
import top.zhaizz.animetracker.common.vo.SubjectDetailVO;
import top.zhaizz.animetracker.common.vo.SubjectListVO;

import java.util.List;

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

    /** 管理员 — 新增条目 */
    SubjectDetailVO createSubject(SubjectCreateDTO request);

    /** 管理员 — 编辑条目 */
    SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request);

    /** 管理员 — 删除条目 */
    void deleteSubject(Long id);
}
