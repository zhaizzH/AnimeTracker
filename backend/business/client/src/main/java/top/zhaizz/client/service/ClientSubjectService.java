package top.zhaizz.client.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.vo.EpisodeVO;
import top.zhaizz.pojo.vo.SubjectDetailVO;
import top.zhaizz.pojo.vo.SubjectListVO;

import java.util.List;

public interface ClientSubjectService {

    PageResult<SubjectListVO> listSubjects(int page, int size, String sort, String order);

    SubjectDetailVO getSubjectDetail(Long id);

    List<EpisodeVO> getEpisodes(Long subjectId);

    PageResult<SubjectListVO> searchSubjects(String keyword, int page, int size);

    PageResult<SubjectListVO> listBySeason(int year, String quarter, int page, int size);

    PageResult<SubjectListVO> listSchedule(int year, String quarter, Integer weekday, int page, int size);
}
