package top.zhaizz.admin.service;

import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.vo.SubjectDetailVO;

/**
 * 番剧管理服务接口
 */
public interface AdminSubjectService {
    /**
     * 创建新番剧
     */
    SubjectDetailVO createSubject(SubjectCreateDTO request);
    /**
     * 更新指定番剧
     */
    SubjectDetailVO updateSubject(Long id, SubjectUpdateDTO request);
    /**
     * 删除指定番剧
     */
    void deleteSubject(Long id);
}
