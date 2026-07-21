package top.zhaizz.admin.service;

import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.vo.SubjectDetailVO;

public interface AdminSubjectService {
    SubjectDetailVO createSubject(SubjectCreateDTO request);
    SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request);
    void deleteSubject(Long id);
}
